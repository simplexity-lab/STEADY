import argparse
import json
import os
from tqdm import tqdm

import numpy as np
import torch
import torch.optim as optim
from torch.utils.data import DataLoader
# from torch.utils.tensorboard import SummaryWriter
import wandb
import time
import torch.nn.functional as F
torch.backends.cudnn.benchmark = True

from model import CILRS
from data import CARLA_Data
from config import GlobalConfig

import wandb
import gc
import sys, os
import pickle
from team_code.mmfn_utils.datasets.dataloader import PRE_Data
from team_code.mmfn_utils.datasets.data_utils import collate_single_cpu_fake
from run_steps.utils import *

parser = argparse.ArgumentParser()
parser.add_argument('--id', type=str, default='new_cilrs', help='Unique experiment identifier.')
parser.add_argument('--device', type=str, default='cuda', help='Device to use')
parser.add_argument('--epochs', type=int, default=151, help='Number of train epochs.')
parser.add_argument('--val_every', type=int, default=5, help='Validation frequency (epochs).')
parser.add_argument('--batch_size', type=int, default=128, help='Batch size')
parser.add_argument('--logdir', type=str, default='log', help='Directory to log data to.')
parser.add_argument('--wandb_mode', type=str, default='online', help='[offline, dryrun, run, disabled, online]')
parser.add_argument('--absolute_path', type=str, default='/home/kin/transfuser/')
parser.add_argument('--save_every', type=int, default=20)

args = parser.parse_args()
args.logdir = os.path.join(args.logdir, args.id)

# writer = SummaryWriter(log_dir=args.logdir)


class Engine(object):
	"""Engine that runs training and inference.
	Args
		- cur_epoch (int): Current epoch.
		- print_every (int): How frequently (# batches) to print loss.
		- validate_every (int): How frequently (# epochs) to run validation.
	"""

	def __init__(self,  cur_epoch=0, bestval_epoch=0):
		self.cur_epoch = cur_epoch
		self.cur_iter = 0
		self.bestval_epoch = bestval_epoch
		self.train_loss = []
		self.val_loss = []
		self.bestval = 1e10

	def train(self, dataloader_train):
		loss_epoch = 0.
		num_batches = 0
		model.train()

		total_num = len(dataloader_train)
		# Train loop
		for cur_num, data in enumerate(dataloader_train):
			
			# efficiently zero gradients
			for p in model.parameters():
				p.grad = None
			
			# create batch and move to GPU
			fronts_in = data['fronts']
			fronts = []
			for i in range(config.seq_len):
				fronts.append(fronts_in[i].to(args.device, dtype=torch.float32))

			# driving labels
			command = data['command'].to(args.device)
			gt_velocity = data['velocity'].to(args.device, dtype=torch.float32)
			gt_steer = data['steer'].to(args.device, dtype=torch.float32)
			gt_throttle = data['throttle'].to(args.device, dtype=torch.float32)
			gt_brake = data['brake'].to(args.device, dtype=torch.float32)

			# inference
			encoding = [model.encoder(fronts)]

			steer, throttle, brake, velocity = model(encoding, gt_velocity, command)
			
			# losses
			loss = 0.05 * F.l1_loss(velocity.squeeze(), gt_velocity).mean()
			loss += F.l1_loss(steer.squeeze(), gt_steer.squeeze()).mean()
			loss += F.l1_loss(throttle.squeeze(), gt_throttle.squeeze()).mean()
			loss += F.l1_loss(brake.squeeze(), gt_brake.squeeze()).mean()
			loss.backward()
			loss_epoch += float(loss.item())

			num_batches += 1
			optimizer.step()

			wandb.log({"loss": loss.item(),"iter": self.cur_iter})
			self.cur_iter += 1
			print(f"Epoch {self.cur_epoch+1} progress: {cur_num:d}/{total_num:d}", end="\r")
		
		
		loss_epoch = loss_epoch / num_batches
		self.train_loss.append(loss_epoch)
		self.cur_epoch += 1

	def validate(self, dataloader_val):
		model.eval()

		with torch.no_grad():	
			num_batches = 0
			vel_epoch = 0.
			steer_epoch = 0.
			throttle_epoch = 0.
			brake_epoch = 0.

			# Validation loop
			for batch_num, data in enumerate(dataloader_val, 0):

				# create batch and move to GPU
				fronts_in = data['fronts']
				fronts = []

				for i in range(config.seq_len):
					fronts.append(fronts_in[i].to(args.device, dtype=torch.float32))

				# driving labels
				command = data['command'].to(args.device)
				gt_velocity = data['velocity'].to(args.device, dtype=torch.float32)
				gt_steer = data['steer'].to(args.device, dtype=torch.float32)
				gt_throttle = data['throttle'].to(args.device, dtype=torch.float32)
				gt_brake = data['brake'].to(args.device, dtype=torch.float32)

				# inference
				encoding = [model.encoder(fronts)]

				steer, throttle, brake, velocity = model(encoding, gt_velocity, command)

				# losses		
				vel_epoch += float(F.l1_loss(velocity.squeeze(), gt_velocity.squeeze()).mean())
				steer_epoch += float(F.l1_loss(steer.squeeze(), gt_steer.squeeze()).mean())
				throttle_epoch += float(F.l1_loss(throttle.squeeze(), gt_throttle.squeeze()).mean())
				brake_epoch += float(F.l1_loss(brake.squeeze(), gt_brake.squeeze()).mean())

				num_batches += 1
					
			vel_loss = vel_epoch / float(num_batches)
			steer_loss = steer_epoch / float(num_batches)
			throttle_loss = throttle_epoch / float(num_batches)
			brake_loss = brake_epoch / float(num_batches)
			print(f'Epoch {self.cur_epoch:03d}, Batch {batch_num:03d}:' +
			f' Vel: {vel_loss:3.3f} Str: {steer_loss:3.3f} Thr: {throttle_loss:3.3f} Brk: {brake_loss:3.3f}')
			count_loss = 0.05 * vel_loss + steer_loss + throttle_loss + brake_loss
			
			wandb.log({"val loss": count_loss,"iter": self.cur_epoch})
			self.val_loss.append(count_loss)

	def save(self):

		save_best = False
		if self.val_loss[-1] <= self.bestval:
			self.bestval = self.val_loss[-1]
			self.bestval_epoch = self.cur_epoch
			save_best = True
		
		# Create a dictionary of all data to save
		log_table = {
			'epoch': self.cur_epoch,
			'iter': self.cur_iter,
			'bestval': self.bestval,
			'bestval_epoch': self.bestval_epoch,
			'train_loss': self.train_loss,
			'val_loss': self.val_loss,
		}
	
		if save_best:
			print('====== Overwrote best model ======>')
			torch.save(model.state_dict(), os.path.join(args.logdir, 'best_model.pth'))
			torch.save(optimizer.state_dict(), os.path.join(args.logdir, 'best_optim.pth'))
		
		print('====== Saved recent model ======>')
		# Save the recent model/optimizer states
		torch.save(model.state_dict(), os.path.join(args.logdir, 'model.pth'))
		torch.save(optimizer.state_dict(), os.path.join(args.logdir, 'recent_optim.pth'))
		# Log other data corresponding to the recent model
		with open(os.path.join(args.logdir, 'recent.log'), 'w') as f:
			f.write(json.dumps(log_table))

if __name__ == '__main__':
	try:
		start_time = time.time()
		# Config
		config = GlobalConfig()
		args.data_file = config.root_dir

		config.train_data = os.path.join(args.data_file,'pro_train_f'+args.data_folder.split('/')[1])
		config.val_data = os.path.join(args.data_file,'pro_eval_f'+args.data_folder.split('/')[1])
		
		# Data
		train_set = PRE_Data(root=config.train_data, config=config, data_use='train')
		val_set = PRE_Data(root=config.val_data, config=config, data_use='val')

		dataloader_train = DataLoader(train_set, batch_size=args.batch_size, shuffle=True, num_workers=8, pin_memory=True, collate_fn = collate_single_cpu_fake)
		dataloader_val = DataLoader(val_set, batch_size=args.batch_size, shuffle=False, num_workers=8, pin_memory=True, collate_fn = collate_single_cpu_fake)

		# Model
		model = CILRS(config, args.device)
		optimizer = optim.AdamW(model.parameters(), lr=config.lr)
		trainer = Engine()

		model_parameters = filter(lambda p: p.requires_grad, model.parameters())
		params = sum([np.prod(p.size()) for p in model_parameters])
		print ('Total trainable parameters: ', params)

		# Create logdir
		if not os.path.isdir(args.logdir):
			os.makedirs(args.logdir)
			print ('Created dir:', args.logdir)
		elif os.path.isfile(os.path.join(args.logdir, 'recent.log')):
			print ('Loading checkpoint from ' + args.logdir)
			with open(os.path.join(args.logdir, 'recent.log'), 'r') as f:
				log_table = json.load(f)

			# Load variables
			trainer.cur_epoch = log_table['epoch']
			trainer.bestval = log_table['bestval']
			trainer.bestval_epoch = log_table['bestval_epoch']
			trainer.train_loss = log_table['train_loss']
			trainer.val_loss = log_table['val_loss']

			# Load checkpoint
			model.load_state_dict(torch.load(os.path.join(args.logdir, 'model.pth')))
			optimizer.load_state_dict(torch.load(os.path.join(args.logdir, 'recent_optim.pth')))
		
		
		wandb.init(project="best_data", entity="mmfn", config = args, mode=args.wandb_mode)
		wandb.watch(model)
		# Log args
		with open(os.path.join(args.logdir, 'args.txt'), 'w') as f:
			json.dump(args.__dict__, f, indent=2)

		for epoch in range(trainer.cur_epoch, args.epochs): 
			epoch_t_start = time.time()
			trainer.train(dataloader_train)

			print("--------------------------------------------------------")
			print("Epoch: ", epoch+1)
			print("  --Train avg loss: %.4f" % trainer.train_loss[-1])
			print("  --Epoch time	: %.2f mins" % ((time.time() - epoch_t_start)/60))
			print("--------------------------------------------------------")
			wandb.log({"spend time": ((time.time() - epoch_t_start)/60),"epoch": epoch})
			if epoch % args.val_every == 0: 
				trainer.validate(dataloader_val)
				if epoch % args.save_every == 0:
					trainer.save()
		
		wandb.save(os.path.join(args.logdir, 'best_model.pth'))
		print(f"{bcolors.OKGREEN}TOTAL RUNNING TIME{bcolors.ENDC}: --- %s hours --- Clean Memory %s" % (round((time.time() - start_time)/3600,2), gc.collect()))
		wandb.finish()
	except Exception as e:
		print("> {}\033[0m\n".format(e))
		torch.cuda.empty_cache()
		print("This script stop as except")
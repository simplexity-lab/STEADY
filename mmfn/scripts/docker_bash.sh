#source ~/anaconda3/etc/profile.d/conda.sh
#conda activate mmfn
cd /home/simplexity/mjw/mmfn


export CODE_FOLDER=/home/simplexity/mjw/mmfn
export CARLA_ROOT=/home/simplexity/mjw/mmfn
export SCENARIO_RUNNER_ROOT=${CODE_FOLDER}/scenario_runner
export LEADERBOARD_ROOT=${CODE_FOLDER}/leaderboard
export PYTHONPATH="${CARLA_ROOT}/carla/":"${SCENARIO_RUNNER_ROOT}":"${LEADERBOARD_ROOT}":"${CARLA_ROOT}/carla/dist/carla-0.9.10-py3.7-linux-x86_64.egg":"${CODE_FOLDER}/team_code":${PYTHONPATH}


python run_steps/phase0.1_Physical.py --config-name=eval
#copy above to the terminal to run evaluate, synchronize mode is True now

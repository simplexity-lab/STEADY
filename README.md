# **SAFEVAR**

## **Description**
Autonomous driving systems (ADSs) must be sufficiently tested to ensure their safety. Though various ADS testing methods have shown promising results, they are limited to a fixed vehicle characteristics setting (VCS). The impact of variations in vehicle characteristics (e.g., mass, tire friction) on the safety of ADSs has not been sufficiently and systematically studied. Such variations are often due to wear and tear, production errors, etc., which may lead to unexpected driving behaviours of ADSs. To this end, in this paper, we propose a method, named SAFEVAR, to systematically find minimum variations to the original vehicle characteristics setting, which affect the safety of the ADS deployed on the vehicle. To evaluate the effectiveness of SAFEVAR, we employed two ADSs and conducted experiments with two driving scenarios. Results show that SAFEVAR, equipped with NSGA-II, generates more critical VCSs that put the vehicle into unsafe situations, as compared with the baseline algorithm. We also identified critical vehicle characteristics and reported to which extent varying their settings put the ADS vehicle into unsafe situations.

This repository contains:

1. **DataSet** : all the raw data for the analyses (including two settings);
2. **Source code** of the scenario designed in the CARLA simulator and the code of the combination of the extended WOR and NSGA-II algorithm (RS); The "**WorldOnRails2.0**" and "**mmfn**" folder contains relevant experiments and documents for Carla Sun (Carla Rain) experiment;
4. **Supplement**: We have provided supplementary data for RQ3.3 (in the paper) in the "Supplement" folder;



## **Contributions**
We extended this work from the following aspects:
- We proposed SAFEVAR to generate variations to vehicle characteristics that threaten the safety of the ADS (not the Automatic Emergency Brake operation); 
- We designed more realistic driving scenarios (e.g., pedestrians crossing the road); 
- With the CARLA simulator, we conducted experiments considering two different weather conditions; 
- To more comprehensively evaluate SAFEVAR, we introduced more safety metrics in addition to the safety metric safetyDegree that we use to drive the search (i.e., Time Exposed Time-to-collision (TET) and Time Integrated Time-to-collision (TIT)).

## **Prerequisite**
- [CARLA 0.9.10](https://carla.readthedocs.io/en/0.9.10/)  
- [jMetalPy](https://github.com/jMetal/jMetalPy)
- **Python** :for World On Rails, you should refer to the [World On Rails](https://github.com/dotchen/WorldOnRails/blob/release/docs/INSTALL.md) to set up environment and the [WordOnRail2.0 README]() to run program; for MMFN, you should refer to [MMFN](https://github.com/Kin-Zhang/mmfn) to set up the environment and run program;

## People
- Qi Pan
- Paolo Arcaini http://group-mmm.org/~arcaini/
- Tao Yue
- Tiexin Wang 
- Jianwei Ma

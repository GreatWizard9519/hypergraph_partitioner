#!/usr/bin/python3
import subprocess
import ntpath
import argparse
import time
import re
import math
import os
import os.path
from threading import Timer
import signal

###################################
# SETUP ENV
###################################
algorithm = "PaToH-S"
preset = "S"
patoh = os.environ.get("PATOH")
###################################

parser = argparse.ArgumentParser()
parser.add_argument("graph", type=str)
parser.add_argument("k", type=int)
parser.add_argument("epsilon", type=float)
parser.add_argument("seed", type=int)
parser.add_argument("objective", type=str)
parser.add_argument("timelimit", type=int)

args = parser.parse_args()

if args.objective == "cut":
  objective = "U"
elif args.objective == "km1":
  objective = "O"

# Run PaToH-S
patoh_proc = subprocess.Popen([patoh,
                               args.graph,
                               str(args.k),
                               'FI='+str(args.epsilon), # imbalance ratio
                               'PQ=' + preset, # preset
                               'SD=' + str(args.seed), # seed
                               'OD=1', # non verbose output
                               'UM=' + objective, # connectivity metric
                               'WI=0', # dont write the partitioning info to disk
                               'BO=C', # balance on cell
                               'A0=100', #  MemMul_CellNet
                               'A1=100', #  MemMul_Pins
                               'A2=100', #  MemMul_General
                              ], stdout=subprocess.PIPE, universal_newlines=True)

def kill_proc():
	patoh_proc.terminate() #signal.SIGTERM

t = Timer(args.timelimit, kill_proc)
t.start()
out, err = patoh_proc.communicate()
t.cancel()
end = time.time()

total_time = 2147483647
cut = 2147483647
km1 = 2147483647
imbalance = 1.0
timeout = "no"
failed = "no"

if patoh_proc.returncode == 0:
  # Extract metrics out of PaToH output
  for line in out.split('\n'):
    s = str(line).strip()
    if ("Cells" in s):
      t = re.compile('Cells : \s*([^\s]*)')
      numHNs = int(str(t.findall(s)[0]))
    if ("'Con - 1' Cost" in s):
      km1 = int(s.split("'Con - 1' Cost:")[1])
    if ("Cut Cost" in s):
      cut = int(s.split("Cut Cost:")[1])
    if ("Part Weights" in s):
      t = re.compile('Min=\s*([^\s]*)')
      min_part = float(t.findall(s)[0])
      t = re.compile('Max=\s*([^\s]*)')
      max_part = float(t.findall(s)[0])
      imbalance = float(max_part) / math.ceil(float(numHNs) / args.k) - 1.0
    if ("Total   " in s):
      t = re.compile('Total\s*:\s*([^\s]*)')
      total_time = float(t.findall(s)[0])
elif patoh_proc.returncode == -signal.SIGTERM:
  timeout = "yes"
else:
  failed = "yes"

# CSV format: algorithm,graph,timeout,seed,k,epsilon,num_threads,imbalance,totalPartitionTime,objective,km1,cut,failed
print(algorithm,
      ntpath.basename(args.graph),
      timeout,
      args.seed,
      args.k,
      args.epsilon,
      1,
      imbalance,
      total_time,
      args.objective,
      km1,
      cut,
      failed,
      sep=",")
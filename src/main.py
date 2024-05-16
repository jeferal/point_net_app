import torch

from time import sleep

def main():

  assert torch.cuda.is_available(), "CUDA is not available"

  print("CUDA is available")

  sleep(1)

if __name__ == "__main__":
  main()

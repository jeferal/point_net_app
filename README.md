# Point Net Suite
Setting up environment to work with point nets.

## Usage
### Build
This script builds and creates the docker image.
```bash
. build.sh
```
### Run
The run script creates the container and executes a script that is located in
the 3D point net repo (it is just a test). It also mounts a data directory
so that we do not need to copy the dataset to the container.
```bash
. run.sh
```

# TODO
* Script to download dataset
* Train, inference, validation pypelines/scripts
* Source code :)

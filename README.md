# Hypervolume
This scorer calculates the hypervolume indicator.

## Usage
```
$ python hv.py '{"objective": [1, 0]}' '[{"objective": [0, 1]}, {"objective": [0.5, 0.5]}]'
0.25
```

## Environmental Variables
The reference point can be specified via `HV_REF_POINT` environmental variable, which should be a vector.

If you need a 2D-hypervolume with reference point `[1, 1]`, then set:
```
HV_REF_POINT="[1, 1]"
```

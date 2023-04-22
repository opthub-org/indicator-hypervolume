#!/bin/env python
"""Test docker image"""
import docker


client = docker.from_env()
c = client.containers.run(
    image="opthub/hypervolume",
    command=["vv"],
    stdin_open=True,
    detach=True,
)
s = c.attach_socket(params={"stdin": 1, "stream": 1, "stdout": 1, "stderr": 1})
x = input("x> ") + "\n"
print(x)
xs = input("xs> ") + "\n"
print(xs)
s._sock.sendall((x + xs).encode("utf-8"))  # pylint: disable=protected-access
c.wait()
stdout = c.logs(stdout=True, stderr=False).decode("utf-8")
print(stdout)

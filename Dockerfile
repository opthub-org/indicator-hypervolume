FROM pagmo2/manylinux228_x86_64_with_deps
COPY . /bench
WORKDIR /bench
RUN yum install -y python39
RUN pip3 install -U pip && pip3 install -r requirements.txt
ENTRYPOINT ["python3", "hv.py"]

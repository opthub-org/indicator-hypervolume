FROM mikebentley15/pagmo2:2.11.3
COPY . /usr/src/app
WORKDIR /usr/src/app
ENTRYPOINT ["python3", "hv.py"]

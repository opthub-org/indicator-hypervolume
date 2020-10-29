FROM mikebentley15/pagmo2:2.11.3
ENV LC_ALL=C.UTF-8 LANG=C.UTF-8
COPY . /bench
WORKDIR /bench
RUN pip3 install -r requirements.txt
ENTRYPOINT ["python3", "hv.py"]

FROM bethgelab/deeplearning:cuda8.0-cudnn6

USER root

RUN apt-get update -qq \
 && DEBIAN_FRONTEND=noninteractive apt-get install -yq -qq --no-install-recommends \
     hdf5-helpers \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip3 --no-cache-dir install --upgrade \
    h5py \
    seaborn \
    jupyterlab \
    torch \
    torchvision

COPY run_jupyterlab.sh /usr/local/bin
RUN chmod +x /usr/local/bin/run_jupyter.sh \
 && chmod -R a+rwx /usr/.jupyter \
 && chmod +x /usr/local/bin/run_jupyterlab.sh

RUN echo "cd /gpfs01/bethge/home/sschneider" >> /root/.bashrc

USER $NB_USER

CMD ["/usr/local/bin/run_jupyterlab.sh"]

FROM ubuntu:16.04

# Install the latest version of R
RUN echo "deb http://cloud.r-project.org/bin/linux/ubuntu xenial/" >> /etc/apt/sources.list

#Add a key to the system so that apt can perform signature checking of the Release File for the added repository to verify its authenticity. The CRAN repository for Ubuntu is signed with the key of “Michael Rutter marutter@gmail.com” with key ID E084DAB9. 

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9

RUN apt-get -y update --allow-unauthenticated && apt-get install -y --no-install-recommends \
    wget \
    r-base \
    r-base-dev \
    ca-certificates
    
RUN R -e "install.packages(c('reshape2', 'recommenderlab', 'plumber', 'dplyr', 'jsonlite'), quiet = TRUE)"

COPY Recommender.R /opt/ml/Recommender.R
COPY plumber.R /opt/ml/plumber.R

ENTRYPOINT ["/usr/bin/Rscript", "/opt/ml/Recommender.R", "--no-save"]

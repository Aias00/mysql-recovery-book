FROM mysql@sha256:0f51e63e537a1f176423fa03ef559aabe6fa4372a53160a44bc7e75da7d15364
# Only extraction uses cpio. The actual mysqlbinlog comes from an exact Oracle
# client RPM whose SHA-256 is checked by run.py before this build.
COPY client.rpm /tmp/client.rpm
RUN microdnf install -y cpio && \
    cd /tmp && rpm2cpio client.rpm | cpio -id ./usr/bin/mysqlbinlog && \
    cp /tmp/usr/bin/mysqlbinlog /usr/local/bin/mysqlbinlog && \
    rm -rf /tmp/client.rpm /tmp/usr && microdnf clean all

FROM fedora:25

RUN dnf install -y --setopt=tsflags=nodocs && \
    dnf -y clean all

LABEL summary="Testing Summary." \
    version="1.0" \
    description="DESCRIPTION." \
    io.k8s.description="IO_K8S_DESCRIPTION." \
    io.k8s.display-name="IO_K8S_DISPLAY_NAME." \
    io.openshift.expose-services="1234:EXPOSE_SERVICES" \
    io.openshift.tags="TAGS"

MAINTAINER "Foo Bar" <foo@bar.com>

ENV POSTFIX_SMTP_PORT=10025

ADD files /files


EXPOSE 1234 2345
EXPOSE 6789

# Postfix UID based from Fedora
# USER 89

VOLUME ['/var/log', '/var/spool/log']
VOLUME ['/var/spool/mail']

CMD ["/files/start.sh"]
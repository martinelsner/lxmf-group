FROM alpine:3.21

RUN apk add --no-cache openrc bash procps git curl

RUN mkdir -p /run/openrc && touch /run/openrc/softlevel

COPY . /opt/lxmf-group-installer

CMD ["tail", "-f", "/dev/null"]
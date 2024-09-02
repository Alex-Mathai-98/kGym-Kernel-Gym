FROM rabbitmq:3.12-management
COPY ./kmq/rabbitmq.conf /etc/rabbitmq/rabbitmq.conf
COPY ./kmq/definitions.json /etc/rabbitmq/definitions.json
ENV RABBITMQ_CONFIG_FILE /etc/rabbitmq/rabbitmq.conf
RUN chmod 644 /etc/rabbitmq/rabbitmq.conf && chmod 644 /etc/rabbitmq/definitions.json

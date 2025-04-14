from rabbitmq_amqp_python_client import Environment

# ...

# create the environment instance
environment = Environment("amqp://guest:guest@localhost:5672/")
# ...
# close the environment when the application stops
environment.close()
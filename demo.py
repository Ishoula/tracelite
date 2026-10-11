from tracelite.logger import TraceLite, trace_errors

logger = TraceLite(
    level="DEBUG",
    format="console",
)

logger.info(
    "Application started",
    context={"service": "student-tracker"},
)
@trace_errors(logger, context={"operation": "calculate"})
def divide(a, b):
    return a / b

try:
    divide(10, 0)
except ZeroDivisionError:
    print("The error was recorded and handled by the demo.")

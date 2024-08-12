# Elastic APM client configuration
from elasticapm import Client as ApmClient
from dotenv import load_dotenv

load_dotenv()

class SingletonApmClient:
    __instance = None

    def __init__(self):
        if not SingletonApmClient.__instance:
            SingletonApmClient.__instance = ApmClient({
                'SERVICE_NAME': os.getenv('ELASTIC_APM_SERVICE_NAME'),
                'SERVER_URL': os.getenv('ELASTIC_APM_SERVER_URL'),
                'ENVIRONMENT': os.getenv('ELASTIC_APM_ENVIRONMENT'),
                'SECRET_TOKEN': os.getenv('ELASTIC_APM_SECRET_TOKEN')
                'VERIFY_SERVER_CERT': False
            })

    @staticmethod
    def get_instance():
        if not SingletonApmClient.__instance:
            SingletonApmClient()
        return SingletonApmClient.__instance


singleton_apm_client = SingletonApmClient.get_instance()

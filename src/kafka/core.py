from confluent_kafka import Producer
import json
import time

from config import settings
from schemas.kafka_task import KafkaTask


class KafkaTaskProducer:
    def __init__(self, host: str, port: int, topic: str):
        self.conf = {
            'bootstrap.servers': f'{host}:{port}',
            # 100MB (увеличьте при необходимости)
            'message.max.bytes': 104857600,
            'compression.type': 'snappy',    # или 'gzip', 'lz4'
            'acks': 'all',                   # гарантия доставки
            'retries': 5,                    # количество попыток
            'linger.ms': 5,                  # задержка перед отправкой
            'queue.buffering.max.messages': 100000,
            'queue.buffering.max.kbytes': 1048576,
            'batch.num.messages': 10000,
            'socket.keepalive.enable': True
        }
        self.topic = topic
        self.producer = Producer(self.conf)

    def delivery_report(self, err, msg):
        """ 
        Callback-функция для обработки результатов доставки сообщения 
        """
        if err is not None:
            print(f'Ошибка доставки сообщения: {err}')
        else:
            print(
                f'Сообщение доставлено в топик {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}')

    def add_task(self, task_data: KafkaTask, key=None):
        """
        Добавление задачи в очередь Kafka

        :param task_data: Данные задачи (словарь или объект, который можно сериализовать в JSON)
        :param key: Ключ сообщения (опционально)
        """
        try:
            data = task_data.model_dump()
            # Сериализация данных в JSON
            value = json.dumps(data).encode('utf-8')

            # Отправка сообщения
            self.producer.produce(
                topic=self.topic,
                key=key,
                value=value,
                callback=self.delivery_report
            )

            # Ожидание подтверждения доставки
            self.producer.flush()

        except Exception as e:
            print(f'Ошибка при отправке задачи: {e}')

    def close(self):
        """ Закрытие соединения с Kafka """
        self.producer.flush()
        print("Соединение с Kafka закрыто")


producer_kafka = KafkaTaskProducer(
    settings.KAFKA_HOST,
    settings.KAFKA_PORT,
    settings.KAFKA_TOPIC
)

# try:
#     # Пример добавления задач
#     for i in range(1, 6):
#         task = {
#             'task_id': i,
#             'task_name': f'Task {i}',
#             'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
#             'payload': {'data': f'sample data {i}'}
#         }

#         print(f"Отправка задачи: {task['task_name']}")
#         producer.add_task(task, key=str(i))
#         time.sleep(1)  # Небольшая задержка между сообщениями

# except KeyboardInterrupt:
#     print("Прервано пользователем")
# finally:
#     producer.close()

import pprint
from pipeline import SchedyPipeline

text = "Добавь встречу на завтра с Сергеем в 16:00"

pipeline = SchedyPipeline()
result = pipeline.process_text(text)
event_result = pipeline.process_and_create_event(text)

print("Результат обработки текста:")
pprint.pprint(result)

print("\nРезультат создания события в календаре:")
pprint.pprint(event_result)
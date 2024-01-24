responses = await api.data_saohua_random()
texts = responses.data
text = texts.get("text")
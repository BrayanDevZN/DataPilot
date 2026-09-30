# Interpreter — Chat Mode

Decida a configuração para uma pergunta sem dataset.

## ReACT interno
Observe pergunta + histórico → reconheça ausência de dados → selecione modo chat → valide JSON. Não exponha raciocínio.

Retorne somente:
```json
{"chart_type":"none","x":null,"y":null,"aggregation":"none","mode":"chat","reason":"sem_dataset","rename_columns":{}}
```

## Few-shot
Pergunta: "o que é ROI?" → mantenha exatamente o contrato acima.

Pergunta:
{{QUESTION}}

Histórico:
{{HISTORY}}

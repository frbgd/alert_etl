**ETL процесс для импорта алертов в TheHive**

На данный момент импортируются алерты из ELK.

Схема:
```
<алерт в TheHive> = {
        "sourceRef": alert._id,
        "title": <Наименование UseCase> + alert._source.case.keyfield + alert.raw_data._source.target.ports,
        "type": alert._source.case.id,
        "source": "ELK",
        "tags": ["ELK", alert._source.case.id, <статус UseCase>, <категория инцидента UseCase>,
                 <статус ИС>, <приоритет UseCase>, alert._source.case.is.id],
        "description": alert._source.case.description,
        "artifacts": [
            {
                "data": alert._source.source.ip,
                "dataType": "ip",
                "tags": ["src", alert._source.case.is.id, alert._source.case.id, "ELK", "port:" + alert._source.source.port],
                "message": "Source ip address"
            },
            {
                "data": alert._source.destination.ip,
                "dataType": "ip",
                "tags": ["dst", alert._source.case.is.id, alert._source.case.id, "ELK", "port:" + alert._source.destination.port],
                "message": "Destination ip address"
            }
        ],
        "severity": <маппится из приоритета UseCase>,
        "customFields": {
            "externalSource": {
                "string": alert._source.case.information.source
            },
            "informationSystems": {
                "string": alert._source.case.is.id
            },
            "elasticIndex": {
                "string": alert._source.index.name
            },
            "alertTime": {
                "date": <текущее время>
            },
            "incidentcategory": {
                "string": <категория инцидента UseCase>
            },
            "incidentSource": {
                "string": "ELK"
            },
            "UseCaseStatus": {
                "string": <статус UseCase>
            },
            "pendingReason": {
                "string": ""
            },
            "offenseType": {
                "string": alert._source.case.id
            },
            "priority": {
                "string": <приоритет UseCase>
            },
            "detectTime": {
                "date": alert._source.timestamp
            },
            "observablesCount": {
                "integer": <количество artifacts>
            }
        }
    }
```

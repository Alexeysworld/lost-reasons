# Pipedrive reference (Midmarket проигрыши)

Всё, что нужно, чтобы тянуть проигранные Midmarket-сделки через MCP **без выгрузки xlsx**.

## Что такое «Midmarket-проигрыш»

Это не отдельный pipeline, а сочетание условий на сделке:
- **pipeline = 53** («SG-сегмент») — поле `field_id 12440`;
- сделка **дошла до встречи**: `entered_stage` IS NOT NULL с `extra_value = 385`
  (этап первой встречи). Это даёт срез «после встречи»;
- **проиграна** в нужном периоде: `lost_time` — поле `field_id 12450`;
- (опц.) исключить служебные этапы: `field_id 12442` (stage_id) `!=` 380, 384, 455.

Поле причины проигрыша: `field_id 12452` (в API v2 — `lost_reason`), значения —
строки вида `"Midmarket: …"`.

## Готовые фильтры (можно переиспользовать)

| filter_id | имя | назначение |
|---|---|---|
| 47454 | «Проигрыши Midmarket после встречи за последние 4 месяца» | основной срез для дайджеста |
| 153211 | «Deal Lost time is last month» | проигрыши за прошлый месяц (pipeline 53 + stage 385) |
| 122763 | «Deal Lost time is this month» | за текущий месяц |

`get_filter(filter_id)` показывает точные условия. Бери за основу 47454/153211.

> ⚠️ Голый «Lost time is last month» (153211) ловит и служебные сделки бывших
> консультантов (loss-комментарий вида «Открытые сделки бывших консов»). Для чистого
> среза используй условия как в 47454 (pipeline 53 + entered_stage 385 + период).

## Период (значения для поля lost_time, field 12450)

`this_month`, `last_month`, `N_months_ago` (напр. `2_months_ago`), либо
оператор `>` со значением даты `after DD.MM.YYYY` (как в фильтре 63791/303773).

## Условия для create_filter (type="deals")

Пример — «проигрыши Midmarket за прошлый месяц после встречи»:

```json
{"glue":"and","conditions":[
 {"glue":"and","conditions":[
   {"object":"deal","field_id":"12440","operator":"=","value":"53","json_value_flag":false},
   {"object":"deal","field_id":"12450","operator":"=","value":"last_month","json_value_flag":false},
   {"object":"deal","field_id":"entered_stage","operator":"IS NOT NULL","extra_value":"385","value":null,"json_value_flag":false},
   {"object":"deal","field_id":"12442","operator":"!=","value":"380","json_value_flag":false},
   {"object":"deal","field_id":"12442","operator":"!=","value":"384","json_value_flag":false},
   {"object":"deal","field_id":"12442","operator":"!=","value":"455","json_value_flag":false}
 ]},
 {"glue":"or","conditions":[]}
]}
```

## Коды кастом-полей сделки (custom_fields в get_deals/get_deal)

| код | колонка (как в xlsx) |
|---|---|
| `lost_reason` (верхний уровень, не в custom_fields) | Deal - Причина проигрыша |
| `96ebda3be9b5a94e1290d7b970d46f99c5204176` | Коммент при проигрыше Midmarket |
| `f49270833b9e1bf32bb8c93c646cef95919f6156` | Конкурент: что используют сейчас / какого выбрали |
| `6115f35a4f1b6589e0d6ae7fd59e70b3fe66527c` | Цели клиента из первой встречи |
| `8db38b8f9384d4c59d93059c9584c469ee0b05e6` | Сильные стороны текущего стека |
| `c587a6ed9abe2da427f39a0b01f64ded31f51011` | Слабые стороны текущего стека |
| `2bd308ae3877abeba0d9d8f30ceab9bbba646963` | Уровень сделки (enum) |
| `af70f9391eeba6e8849e5de4bf671c05dfa80a33` | Источник продажи (enum) |

Верхний уровень сделки также даёт: `id`, `title`, `stage_id`, `pipeline_id`,
`status`, `lost_time`, `value`, `org_id`, `person_id`.

> Коды кастом-полей стабильны, но при сомнении сверяй `list_deal_fields`
> (поле `field_code`). enum-значения (Уровень сделки/Источник) приходят id'шниками —
> при необходимости резолвь по `options` из `list_deal_fields`.

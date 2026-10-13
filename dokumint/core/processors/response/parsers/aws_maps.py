class AWSMaps():
    """
    :TODO: Improve this comment
    Class constants representing map of various document elements
    """

    ANALYZE_EXPENSE_MAP = {
        "entities": [
            {
                "entity" : "core.mongo.Creator",
                "field_paths" : {
                    "name" : {
                        "type" : "mongoengine.StringField",
                        "extractor" : "extract_simple_field",
                        "converter" : "core.processors.response.parsers.utils.parse_str",
                        "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='VENDOR_NAME')].ValueDetection.Text"
                    },
                    "logo_uri" : {
                        "type" : "mongoengine.StringField",
                        "extractor" : "extract_simple_field",
                        "converter" : "core.processors.response.parsers.utils.parse_str"
                    },
                    "web_url" : {
                        "type" : "mongoengine.StringField",
                        "extractor" : "extract_simple_field",
                        "converter" : "core.processors.response.parsers.utils.parse_str",
                        "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='VENDOR_URL')].ValueDetection.Text"
                    },
                    "phone" : {
                        "type" : "mongoengine.StringField",
                        "extractor" : "extract_simple_field",
                        "converter" : "core.processors.response.parsers.utils.parse_str",
                        "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='VENDOR_PHONE')].ValueDetection.Text"
                    },
                    "vat_id" : {
                        "type" : "mongoengine.StringField",
                        "extractor" : "extract_simple_field",
                        "converter" : "core.processors.response.parsers.utils.parse_str",
                        "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='VENDOR_VAT_NUMBER')].ValueDetection.Text"
                    },
                    "registration_id" : {
                        "type" : "mongoengine.StringField",
                        "extractor" : "extract_simple_field",
                        "converter" : "core.processors.response.parsers.utils.parse_str"
                    },
                    "other_id" : {
                        "type" : "mongoengine.StringField",
                        "extractor" : "extract_simple_field",
                        "converter" : "core.processors.response.parsers.utils.parse_str",
                        "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='VENDOR_ADDRESS')].ValueDetection.Text"
                    }
                }
            },
            {
                "entity" : "core.mongo.ExpenseDocument",
                "field_paths" : {
                    "addresses" : {
                        "type" : "core.mongo.DocumentAddress",
                        "extractor" : "extract_grouped_nested_field",
                        "group_by" : {
                            "key" : "{id}",
                            "groups_path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='ADDRESS')].GroupProperties[*].Id",
                            "grouped_value_path" : "$.ExpenseDocuments[*].SummaryFields[?@.GroupProperties[?@.Id=='{id}']]"
                        },
                        "field_paths" : {
                            "address_type" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                                "path" : "$[0].GroupProperties[*].Types[0]"
                            },
                            "addressee" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                                "path" : "$[?@.Type.Text=='NAME'].ValueDetection.Text"
                            },
                            "line_1" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                                "path" : "$[?@.Type.Text=='STREET'].ValueDetection.Text"
                            },
                            "line_2" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str"
                            },
                            "city" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                                "path" : "$[?@.Type.Text=='CITY'].ValueDetection.Text"
                            },
                            "state" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                                "path" : "$[?@.Type.Text=='STATE'].ValueDetection.Text"
                            },
                            "postal_code" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                                "path" : "$[?@.Type.Text=='ZIP_CODE'].ValueDetection.Text"
                            },
                            "country" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                                "path" : "$[?@.Type.Text=='COUNTRY'].ValueDetection.Text"
                            }
                        }
                    },
                    "dates" : {
                        "type" : "core.mongo.ExpenseDates",
                        "extractor" : "extract_nested_field",
                        "field_paths" : {
                            "transaction_date" : {
                                "type" : "mongoengine.DateField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_date",
                                "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='INVOICE_RECEIPT_DATE')].ValueDetection.Text"
                            },
                            "due_date" : {
                                "type" : "mongoengine.DateField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_date"
                            },
                            "ship_date" : {
                                "type" : "mongoengine.DateField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_date"
                            },
                            "delivery_date" : {
                                "type" : "mongoengine.DateField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_date"
                            },
                            "start_date" : {
                                "type" : "mongoengine.DateField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_date"
                            },
                            "end_date" : {
                                "type" : "mongoengine.DateField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_date"
                            }
                        }
                    },
                    "financials" : {
                        "type" : "core.mongo.ExpenseFinancials",
                        "extractor" : "extract_nested_field",
                        "field_paths" : {
                            "subtotal" : {
                                "type" : "mongoengine.DecimalField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_float",
                                "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='SUBTOTAL')].ValueDetection.Text"
                            },
                            "discount" : {
                                "type" : "mongoengine.DecimalField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_float",
                                "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='DISCOUNT')].ValueDetection.Text"
                            },
                            "cashback" : {
                                "type" : "mongoengine.DecimalField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_float"
                            },
                            "tip" : {
                                "type" : "mongoengine.DecimalField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_float",
                                "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='GRATUITY')].ValueDetection.Text"
                            },
                            "total" : {
                                "type" : "mongoengine.DecimalField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_float",
                                "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='TOTAL')].ValueDetection.Text"
                            },
                            "balance_due" : {
                                "type" : "mongoengine.DecimalField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_float",
                                "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='AMOUNT_DUE')].ValueDetection.Text"
                            },
                            "currency_code" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_date"
                            }
                        }
                    },
                    "identifiers" : {
                        "type" : "core.mongo.ExpenseIdentifiers",
                        "extractor" : "extract_nested_field",
                        "field_paths" : {
                            "account_id" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                                "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='ACCOUNT_NUMBER')].ValueDetection.Text"
                            },
                            "invoice_id" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                                "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='INVOICE_RECEIPT_ID')].ValueDetection.Text"
                            },
                            "po_id" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                                "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='PO_NUMBER')].ValueDetection.Text"
                            },
                            "reference_id" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                            },
                            "other_id" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                                "path" : "$.ExpenseDocuments[*].SummaryFields[?(@.Type.Text=='TAX_PAYER_ID')].ValueDetection.Text"
                            }
                        }
                    },
                    "line_items" : {
                        "type" : "core.mongo.ExpenseLineItem",
                        "extractor" : "extract_list_of_nested_field",
                        "count" : "$.ExpenseDocuments[*].LineItemGroups[*].LineItems.`len`",
                        "field_paths" : {
                            "date" : {
                                "type" : "mongoengine.DateField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_date"
                            },
                            "sku" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                                "path" : "$.ExpenseDocuments[*].LineItemGroups[*].LineItems[{#}].LineItemExpenseFields[?(@.Type.Text=='PRODUCT_CODE')].ValueDetection.Text"
                            },
                            "upc" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str"
                            },
                            "description" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str",
                                "path" : "$.ExpenseDocuments[*].LineItemGroups[*].LineItems[{#}].LineItemExpenseFields[?(@.Type.Text=='ITEM')].ValueDetection.Text"
                            },
                            "quantity" : {
                                "type" : "mongoengine.DecimalField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_float",
                                "path" : "$.ExpenseDocuments[*].LineItemGroups[*].LineItems[{#}].LineItemExpenseFields[?(@.Type.Text=='QUANTITY')].ValueDetection.Text"
                            },
                            "discount_amt" : {
                                "type" : "mongoengine.DecimalField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_float"
                            },
                            "discount_rate" : {
                                "type" : "mongoengine.DecimalField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_float"
                            },
                            "unit_measure" : {
                                "type" : "mongoengine.StringField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str"
                            },
                            "unit_price" : {
                                "type" : "mongoengine.DecimalField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_float",
                                "path" : "$.ExpenseDocuments[*].LineItemGroups[*].LineItems[{#}].LineItemExpenseFields[?(@.Type.Text=='UNIT_PRICE')].ValueDetection.Text"
                            },
                            "total" : {
                                "type" : "mongoengine.DecimalField",
                                "extractor" : "extract_simple_field",
                                "converter" : "core.processors.response.parsers.utils.parse_str_to_float",
                                "path" : "$.ExpenseDocuments[*].LineItemGroups[*].LineItems[{#}].LineItemExpenseFields[?(@.Type.Text=='PRICE')].ValueDetection.Text"
                            }
                        }
                    },
                    "taxes" : {}
                }
            }
        ]
    }


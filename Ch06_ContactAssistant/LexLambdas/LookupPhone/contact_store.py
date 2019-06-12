import boto3


class ContactStore:
    def __init__(self, store_location):
        self.client = boto3.client('dynamodb')
        self.table_name = store_location

    def save_contact(self, contact_info):
        response = self.client.put_item(
            TableName = self.table_name,
            Item = ContactStore.convert_dict_to_item(contact_info)
        )
        # should return values from dynamodb however,
        # dynamodb does not support ReturnValues = ALL_NEW
        return contact_info

    def get_all_contacts(self):
        contacts = self.client.scan(
            TableName = self.table_name
        )

        contact_info_list = []
        for item in contacts['Items']:
            contact_info_list.append(ContactStore.convert_item_to_dict(item))

        return contact_info_list

    def get_contact_by_name(self, name):
        contact = self.client.get_item(
            TableName = self.table_name,
            Key = ContactStore.convert_dict_to_item({'name': name})
        )

        if 'Item' in contact:
            contact_info = ContactStore.convert_item_to_dict(contact['Item'])
        else:
            contact_info = {}

        return contact_info

    @staticmethod
    def convert_dict_to_item(dictionary):
        if type(dictionary) is dict:
            item = {}
            for k, v in dictionary.items():
                if type(v) is str:
                    item[k] = {
                        'S': v
                    }
                elif type(v) is int:
                    item[k] = {
                        'I': str(v)
                    }
                elif type(v) is dict:
                    item[k] = {
                        'M': ContactStore.dict_to_item(v)
                    }
                elif type(v) is list:
                    item[k] = []
                    for i in v:
                        item[k].append(ContactStore.dict_to_item(i))

            return item
        elif type(dictionary) is str:
            return {
                'S': dictionary
            }
        elif type(dictionary) is int:
            return {
                'I': str(dictionary)
            }

    @staticmethod
    def convert_item_to_dict(item):
        dictionary = {}
        if type(item) is str:
            return item
        for key, struct in item.items():
            if type(struct) is str:
                if key == 'I':
                    return int(struct)
                else:
                    return struct
            else:
                for k, v in struct.items():
                    if k == 'L':
                        value = []
                        for i in v:
                            value.append(ContactStore.convert_item_to_dict(i))
                    elif k == 'S':
                        value = str(v)
                    elif k == 'I':
                        value = int(v)
                    elif k == 'M':
                        value = {}
                        for a, b in v.items():
                            value[a] = ContactStore.convert_item_to_dict(b)
                    else:
                        key = k
                        value = ContactStore.convert_item_to_dict(v)

                    dictionary[key] = value

        return dictionary

import boto3


class ContactStore:
    def __init__(self, store_location):
        self.table = boto3.resource('dynamodb').Table(store_location)

    def save_contact(self, contact_info):
        response = self.table.put_item(
            Item = contact_info
        )
        # should return values from dynamodb however,
        # dynamodb does not support ReturnValues = ALL_NEW
        return contact_info

    def get_all_contacts(self):
        response = self.table.scan()

        contact_info_list = []
        for item in response['Items']:
            contact_info_list.append(item)

        return contact_info_list

    def get_contact_by_name(self, name):
        response = self.table.get_item(
            Key = {'name': name}
        )

        if 'Item' in response:
            contact_info = response['Item']
        else:
            contact_info = {}

        return contact_info

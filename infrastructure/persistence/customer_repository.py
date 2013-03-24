from infrastructure.persistence.repository import Repository
from domain.model.customer.customer import Customer


class CustomerRepository(Repository):
    def __init__(self):
        super(CustomerRepository, self).__init__()

    def find(self, customer_name):
        query = self.session.query(Customer).filter(Customer.name == customer_name)

        return super(CustomerRepository, self).find(query)

    def store(self, customer_entity):
        self.session.add(customer_entity)

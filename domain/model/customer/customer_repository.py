from domain.shared.repository import Repository


class CustomerRepository(Repository):
    def find(self, customer_id):
        raise NotImplementedError()

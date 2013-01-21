import datetime

from unittest import TestCase, skip
from nose.tools import raises

from factories.inventory import InventoryItemFactory
from domain.model.inventory.tracker import *

class InventoryStatesTestCase(TestCase):

    def setUp(self):
        self.machine = TrackingStateMachine()

        # Setup states
        self.machine.add_state(OnHandState("OnHand"))
        self.machine.add_state(CommittedState("Committed"))

        # Add transitions between states
        self.machine.add_transition("commit", "OnHand", "Committed")

    @raises(TypeError)
    def test_invalid_state(self):
        self.machine.add_state(None)

    @raises(ValueError)
    def test_invalid_transition_states(self):
        self.machine.add_transition("commit", "Foo", "Bar")

    @raises(ValueError)
    def test_invalid_transition(self):
        self.machine.add_transition("foobar", "OnHand", "Committed")

    def test_perform_invalid_transition(self):
        self.machine.transition("foobar", None, None)

    def test_transition_commit(self):
        # Test begins here
        self.machine.state("OnHand").track({"quantity": 10, "warehouse": "WHSE001"})
        self.machine.state("Committed").track({"quantity": 5, "warehouse": "WHSE001", "order_id": "ORD001",
                                               "date": datetime.datetime.now()})

        self.assertEquals(10, self.machine.state("OnHand").quantity(), "On Hand quantity not initialised correctly")
        self.assertEquals(5, self.machine.state("Committed").quantity(), "Wrong number of items committed")

        self.machine.transition("commit",
            {"quantity": 5, "warehouse": "WHSE001"},
            {"quantity": 5, "warehouse": "WHSE001", "order_id": "ORD002", "date": datetime.datetime.now()})()

        self.assertEquals(5, self.machine.state("OnHand").quantity(), "On Hand quantity not reduced")
        self.assertEquals(10, self.machine.state("Committed").quantity(), "Wrong number of items committed")

class InventoryOnHandTestCase(TestCase):

    def test_enter_stock_on_hand(self):
        item = InventoryItemFactory.build()

        item.enter_stock_on_hand(10, "WHSE001")

        self.assertEquals(10, item.physical_quantity_on_hand(), "Incorrect on hand count set")

    def test_enter_stock_on_hand_multiple_locations(self):
        item = InventoryItemFactory.build()

        item.enter_stock_on_hand(1, "WHSE001")
        item.enter_stock_on_hand(1, "WHSE001")
        item.enter_stock_on_hand(1, "WHSE002")

        self.assertEquals(3, item.physical_quantity_on_hand(), "Incorrect on hand count for all warehouses")
        self.assertEquals(2, item.physical_quantity_on_hand(warehouse="WHSE001"), "Incorrect on hand count for warehouse 1")
        self.assertEquals(1, item.physical_quantity_on_hand(warehouse="WHSE002"), "Incorrect on hand count for warehouse 2")

    def test_enter_negative_stock(self):
        item = InventoryItemFactory.build()

        item.enter_stock_on_hand(-1, "WHSE001")

        self.assertEquals(0, item.effective_quantity_on_hand(), "Incorrect on hand count set")

class InventoryCommitTestCase(TestCase):

    def test_commit_less_than_on_hand(self):
        item = InventoryItemFactory.build()
        item.enter_stock_on_hand(2, "WHSE001")

        self.assertEquals(2, item.physical_quantity_on_hand(), "Incorrect physical on-hand count set")
        self.assertEquals(2, item.effective_quantity_on_hand(), "Incorrect effective on-hand count set")

        item.commit(1, "WHSE001", "ORD000")

        self.assertEquals(2, item.physical_quantity_on_hand(), "Incorrect physical on-hand count set after commit")
        self.assertEquals(1, item.effective_quantity_on_hand(), "Incorrect effective on-hand count set after commit")

        committed_items = item.find_committed_for_order("ORD000")

        self.assertFalse(committed_items == {}, "No items were committed")
        self.assertEqual(1, item.quantity_committed(), "Not exactly one item was committed")
        self.assertEquals(1, item.quantity_committed(warehouse="WHSE001"), "Only one item should have been committed")

    def test_multiple_commit_from_multiple_warehouse_with_backorder(self):
        item = InventoryItemFactory.build()

        item.enter_stock_on_hand(1, "WHSE001")
        item.enter_stock_on_hand(1, "WHSE001")
        item.enter_stock_on_hand(3, "WHSE002")

        self.assertEquals(5, item.physical_quantity_on_hand(), "Incorrect on hand count for all warehouses")
        self.assertEquals(2, item.physical_quantity_on_hand(warehouse="WHSE001"), "Incorrect on hand count for warehouse 1")
        self.assertEquals(3, item.physical_quantity_on_hand(warehouse="WHSE002"), "Incorrect on hand count for warehouse 2")

        item.commit(2, "WHSE001", "ORD001")
        item.commit(1, "WHSE002", "ORD001")

        self.assertEquals(5, item.physical_quantity_on_hand(), "Incorrect physical on-hand count set after commit")
        self.assertEquals(2, item.effective_quantity_on_hand(), "Incorrect effective on-hand count set after commit")
        self.assertEquals(0, item.effective_quantity_on_hand(warehouse="WHSE001"), "Incorrect effective on-hand count set after commit")
        self.assertEquals(2, item.effective_quantity_on_hand(warehouse="WHSE002"), "Incorrect effective on-hand count set after commit")

        committed_items = item.find_committed_for_order("ORD001")

        self.assertFalse(committed_items == {}, "No items were committed")
        self.assertEqual(3, item.quantity_committed(), "Not exactly three items were committed")
        self.assertEquals(2, item.quantity_committed(warehouse="WHSE001"), "Only two items should have been committed")
        self.assertEquals(1, item.quantity_committed(warehouse="WHSE002"), "Only one item should have been committed")

        item.commit(3, "WHSE002", "ORD002")

        self.assertEquals(0, item.effective_quantity_on_hand(), "Incorrect effective on-hand count set after commit")
        self.assertEquals(0, item.effective_quantity_on_hand(warehouse="WHSE002"), "Incorrect effective on-hand count set after commit")
        self.assertEquals(3, item.quantity_committed(warehouse="WHSE002"), "Three items should now be committed")

        self.assertEquals(1, item.quantity_backordered(), "Incorrect number of backorders after commit")
        self.assertEqual(0, item.quantity_backordered(order_id="ORD001"), "ORD001 should not have any backorders")
        self.assertEquals(1, item.quantity_backordered(order_id="ORD002"), "ORD002 should not have backorder qty of 1")

        item.commit(1, "WHSE001", "ORD003")
        item.commit(1, "WHSE002", "ORD004")

        self.assertEquals(0, item.effective_quantity_on_hand(), "Incorrect effective on-hand count set after commit")
        self.assertEquals(2, item.quantity_committed(warehouse="WHSE001"), "2 items should still be committed to WHSE001")
        self.assertEquals(3, item.quantity_committed(warehouse="WHSE002"), "3 items should still be committed to WHSE002")
        self.assertEquals(3, item.quantity_backordered(), "Incorrect number of backorders after commit")
        self.assertEquals(1, item.quantity_backordered(order_id="ORD003"), "ORD003 should now have backorder qty of 1")
        self.assertEquals(1, item.quantity_backordered(order_id="ORD004"), "ORD004 should now have backorder qty of 1")

    def test_backorder_commitment(self):
        item = InventoryItemFactory.build()
        item.enter_stock_on_hand(3, "WHSE001")
        item.commit(2, "WHSE001", "ORD001")

        self.assertEquals(1, item.effective_quantity_on_hand(), "Incorrect effective on-hand count set after commit")
        self.assertEquals(2, item.quantity_committed(warehouse="WHSE001"), "2 items should be committed to WHSE001")

        # Ensure bogus backorders have no effect
        item.backorder_commitment(100, "WHSEXXX", "ORDXXX")
        item.backorder_commitment(100, "WHSEXXX", "ORD001")
        item.backorder_commitment(100, "WHSE001", "ORDXXX")
        self.assertEquals(1, item.effective_quantity_on_hand(), "Incorrect effective on-hand count set after commit")
        self.assertEquals(2, item.quantity_committed(warehouse="WHSE001"), "2 items should be committed to WHSE001")

        # Backorder part of the commitment
        item.backorder_commitment(1, "WHSE001", "ORD001")

        self.assertEquals(1, item.quantity_committed(warehouse="WHSE001"), "Only 1 items should still be committed to")
        self.assertEquals(1, item.quantity_backordered(order_id="ORD001"), "ORD001 should now have backorder qty of 1")

        # Backorder the remainder
        item.backorder_commitment(1, "WHSE001", "ORD001")
        self.assertEquals(0, item.quantity_committed(warehouse="WHSE001"), "Only 1 items should still be committed to")
        self.assertEquals(2, item.quantity_backordered(order_id="ORD001"), "ORD001 should now have backorder qty of 1")

    def test_revert_commitment(self):
        item = InventoryItemFactory.build()
        item.enter_stock_on_hand(3, "WHSE001")

        item.commit(2, "WHSE001", "ORD001")

        item.revert(1, "WHSE001", "ORD001")

        # Ensure bogus reverts don't pass
        item.revert(100, "WHSEXXX", "ORD001")
        item.revert(100, "WHSE001", "ORDXXX")
        item.revert(100, "WHSEXXX", "ORDXXX")

        self.assertEquals(1, item.quantity_committed(warehouse="WHSE001"), "Only 1 commitment should remain after " +
                                                                           "revert")
        self.assertEquals(2, item.effective_quantity_on_hand(), "2 should now be in stock")


class InventoryBackordersTestCase(TestCase):

    def test_fulfill_backorder_partial(self):
        item = InventoryItemFactory.build()

        item.commit(2, "WHSE001", "ORD001")

        self.assertEquals(0, item.effective_quantity_on_hand(), "Warehouse should have no stock")
        self.assertEquals(2, item.quantity_backordered(), "Commit should have created 2 backorders")

        item.enter_stock_on_hand(1, "WHSE001")
        self.assertEquals(1, item.effective_quantity_on_hand(), "Warehouse should have qty of 1 on hand")

        item.fulfill_backorder(1, "WHSE001", "ORD001")
        self.assertEquals(1, item.quantity_backordered(), "Backorder should have been reduced to qty of 1")
        self.assertEquals(1, item.quantity_committed(), "A commitment of 1 item should have been created")
        self.assertEquals(0, item.effective_quantity_on_hand(), "On hand quantity should be 0")

    def test_fulfill_backorder_completely(self):
        item = InventoryItemFactory.build()

        item.commit(2, "WHSE001", "ORD001")

        self.assertEquals(0, item.effective_quantity_on_hand(), "Warehouse should have no stock")
        self.assertEquals(2, item.quantity_backordered(), "Commit should have created 2 backorders")

        item.enter_stock_on_hand(3, "WHSE001")
        self.assertEquals(3, item.effective_quantity_on_hand(), "Warehouse should have qty of 1 on hand")

        item.fulfill_backorder(2, "WHSE001", "ORD001")
        self.assertEquals(0, item.quantity_backordered(), "No backorders should remain")
        self.assertEquals(2, item.quantity_committed(), "A commitment of 2 items should have been created")
        self.assertEquals(1, item.effective_quantity_on_hand(), "On hand quantity of 1 should be remain")

    def test_fulfill_backorder_not_possible(self):
        item = InventoryItemFactory.build()
        item.commit(1, "WHSE001", "ORD001")
        item.enter_stock_on_hand(1, "WHSE001")

        self.assertEquals(1, item.effective_quantity_on_hand(), "Warehouse should have on hand qty of 1")
        self.assertEquals(1, item.quantity_backordered(), "Commit should have created 1 backorder")

        # Impossible fulfillment
        item.fulfill_backorder(2, "WHSE001", "ORD001")
        self.assertEquals(1, item.effective_quantity_on_hand(), "Warehouse qty should not have changed")
        self.assertEquals(1, item.quantity_backordered(), "Backorder qty should not have changed")

    def test_cancel_backorder(self):
        item = InventoryItemFactory.build()
        item.commit(1, "WHSE001", "ORD001")

        self.assertEquals(0, item.effective_quantity_on_hand(), "Warehouse should be empty")
        self.assertEquals(1, item.quantity_backordered(order_id="ORD001"), "Commit should have created 1 backorder")

        item.cancel_backorder("WHSE001", "ORD001")
        item.cancel_backorder("WHSE001", "ORDXXX")

        self.assertEquals(0, item.effective_quantity_on_hand(), "Warehouse should still be empty")
        self.assertEquals(0, item.quantity_backordered(), "Cancel should have removed backorder")

class InventoryFulfilledTestCase(TestCase):

    def test_fulfill_commitment(self):
        item = InventoryItemFactory.build()
        item.enter_stock_on_hand(2, "WHSE001")
        item.commit(2, "WHSE001", "ORD001")

        item.fulfill_commitment(1, "WHSE001", "ORD001", "INV001")

        self.assertEquals(0, item.effective_quantity_on_hand(), "Warehouse should be empty")
        self.assertEquals(1, item.quantity_committed(warehouse="WHSE001"), "One unfilfilled item should remain")
        self.assertEquals(1, item.quantity_fulfilled("INV001"), "Item was not fulfilled")

        invoice = item.find_fulfillment_for_invoice("INV001")
        self.assertEquals(1, invoice.quantity, "Invoice has incorrect quantity")
        self.assertEquals("ORD001", invoice.order_id, "Invoice has incorrect Order")

        # Using the same invoice twice should not commit
        item.fulfill_commitment(1, "WHSE001", "ORD001", "INV001")
        self.assertEquals(0, item.effective_quantity_on_hand(), "Warehouse should be empty")
        self.assertEquals(1, item.quantity_committed(warehouse="WHSE001"), "One unfilfilled item should remain")
        self.assertEquals(1, item.quantity_fulfilled("INV001"), "Item was not fulfilled")

        item.fulfill_commitment(1, "WHSE001", "ORD001", "INV002")
        self.assertEquals(0, item.effective_quantity_on_hand(), "Warehouse should be empty")
        self.assertEquals(0, item.quantity_committed(warehouse="WHSE001"), "One unfilfilled item should remain")
        self.assertEquals(1, item.quantity_fulfilled("INV002"), "Item was not fulfilled")

        self.assertEquals(2, item.quantity_fulfilled(), "Total number of fulfillments incorrect")
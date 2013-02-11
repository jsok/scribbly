import datetime

from unittest import TestCase, skip
from nose.tools import raises

from domain.tests.factories.inventory import InventoryItemFactory
from domain.model.inventory.tracker import *

class InventoryStatesTestCase(TestCase):

    def setUp(self):
        self.machine = TrackingStateMachine()
        self.machine.add_state(OnHandState("OnHand"))
        self.machine.add_state(CommittedState("Committed"))
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
        transition = self.machine.transition("foobar", None, None)
        self.assertIsInstance(transition, type(lambda: None), "Transition was not a null op")

    @raises(ValueError)
    def test_invalid_action(self):
        self.machine.add_action("foobar", "OnHand")

    def test_perform_invalid_action(self):
        action = self.machine.action("foobar", {})
        self.assertIsInstance(action, type(lambda: None), "Action was not a null op")

    def test_perform_action(self):
        # Add a dummy action which always returns True
        self.machine.state("OnHand").foo = lambda x: True
        self.machine.add_action("foo", "OnHand")

        action_func = self.machine.action("foo", {})
        self.assertTrue(action_func(), "Action did not execute correctly")

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

class InventoryCommitNoBufferTestCase(TestCase):

    def test_commit_less_than_on_hand(self):
        item = InventoryItemFactory.build()
        item.enter_stock_on_hand(2, "WHSE001")

        self.assertEquals(2, item.physical_quantity_on_hand(), "Incorrect physical on-hand count set")
        self.assertEquals(2, item.effective_quantity_on_hand(), "Incorrect effective on-hand count set")

        item.commit(1, "WHSE001", "ORD000")

        self.assertEquals(2, item.physical_quantity_on_hand(), "Incorrect physical on-hand count set after commit")
        self.assertEquals(1, item.effective_quantity_on_hand(), "Incorrect effective on-hand count set after commit")

        committed_items = item.find_committed_for_order("ORD000")

        self.assertIsNotNone(committed_items, "No items were committed")
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

        self.assertIsNotNone(committed_items, "No items were committed")
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
        # Over-revert should not pass
        item.revert(10, "WHSE001", "ORD001")

        self.assertEquals(1, item.quantity_committed(warehouse="WHSE001"), "Only 1 commitment should remain after " +
                                                                           "revert")
        self.assertEquals(2, item.effective_quantity_on_hand(), "2 should now be in stock")


class InventoryCommitWithBufferTestCase(TestCase):

    def test_onhand_honours_buffer(self):
        item = InventoryItemFactory.build(on_hand_buffer=1)
        item.enter_stock_on_hand(2, "WHSE001")

        item.commit(2, "WHSE001", "ORD001")

        self.assertEquals(0, item.effective_quantity_on_hand("WHSE001"))

    def test_commit_and_verify(self):
        item = InventoryItemFactory.build(on_hand_buffer=2)
        item.enter_stock_on_hand(5, "WHSE001")

        item.commit(4, "WHSE001", "ORD001")

        self.assertEquals(1, item.effective_quantity_on_hand("WHSE001"))
        self.assertEquals(3, item.find_committed_for_order("ORD001")["WHSE001"].quantity,
                          "Incorrect quantity was automatically verified")
        self.assertEquals(1, item.find_committed_for_order("ORD001")["WHSE001"].unverified_quantity,
                          "Incorrect quantity was automatically verified")

        # Verify the original stock level was correct
        item.verify_stock_level(5, "WHSE001")

        self.assertEquals(1, item.effective_quantity_on_hand("WHSE001"))
        self.assertEquals(4, item.find_committed_for_order("ORD001")["WHSE001"].quantity,
                          "Item quantities do not reflect verification count")
        self.assertEquals(0, item.find_committed_for_order("ORD001")["WHSE001"].unverified_quantity,
                          "Item quantities do not reflect verification count")

    def test_commit_and_verify_with_backorder(self):
        item = InventoryItemFactory.build(on_hand_buffer=2)
        item.enter_stock_on_hand(5, "WHSE001")

        item.commit(6, "WHSE001", "ORD001")

        self.assertEquals(0, item.effective_quantity_on_hand("WHSE001"))
        self.assertEquals(3, item.find_committed_for_order("ORD001")["WHSE001"].quantity,
                          "Incorrect quantity was automatically verified")
        self.assertEquals(2, item.find_committed_for_order("ORD001")["WHSE001"].unverified_quantity,
                          "Incorrect quantity was automatically verified")
        self.assertEquals(1, item.quantity_backordered("ORD001"), "Item was not backordered")

        # Verify the original stock level was correct
        item.verify_stock_level(5, "WHSE001")

        self.assertEquals(0, item.effective_quantity_on_hand("WHSE001"))
        self.assertEquals(5, item.find_committed_for_order("ORD001")["WHSE001"].quantity,
                          "Item quantities do not reflect verification count")
        self.assertEquals(0, item.find_committed_for_order("ORD001")["WHSE001"].unverified_quantity,
                          "Item quantities do not reflect verification count")
        self.assertEquals(1, item.quantity_backordered("ORD001"), "Backorder should not have been modified")

    def test_commit_with_verify_discrepancy(self):
        item = InventoryItemFactory.build(on_hand_buffer=2)
        item.enter_stock_on_hand(5, "WHSE001")

        item.commit(4, "WHSE001", "ORD001")

        self.assertEquals(1, item.effective_quantity_on_hand("WHSE001"))
        self.assertEquals(3, item.find_committed_for_order("ORD001")["WHSE001"].quantity,
                          "Incorrect quantity was automatically verified")
        self.assertEquals(1, item.find_committed_for_order("ORD001")["WHSE001"].unverified_quantity,
                          "Incorrect quantity was automatically verified")

        # We could only find 3, 2 went missing!
        item.verify_stock_level(3, "WHSE001")

        self.assertEquals(0, item.effective_quantity_on_hand("WHSE001"))
        self.assertEquals(3, item.find_committed_for_order("ORD001")["WHSE001"].quantity,
                          "Item quantities do not reflect verification count")
        self.assertEquals(0, item.find_committed_for_order("ORD001")["WHSE001"].unverified_quantity,
                          "Item quantities do not reflect verification count")
        self.assertEquals(1, item.quantity_backordered("ORD001"), "Backorder should have been created")
        self.assertEquals(2, item.quantity_lost(), "Incorrect number of lost items tracked")

    def test_commit_with_major_verify_discrepancy(self):
        item = InventoryItemFactory.build(on_hand_buffer=2)
        item.enter_stock_on_hand(5, "WHSE001")

        item.commit(4, "WHSE001", "ORD001")

        self.assertEquals(1, item.effective_quantity_on_hand("WHSE001"))
        self.assertEquals(3, item.find_committed_for_order("ORD001")["WHSE001"].quantity,
                          "Incorrect quantity was automatically verified")
        self.assertEquals(1, item.find_committed_for_order("ORD001")["WHSE001"].unverified_quantity,
                          "Incorrect quantity was automatically verified")

        # All 5 went missing!
        item.verify_stock_level(0, "WHSE001")

        self.assertEquals(0, item.effective_quantity_on_hand("WHSE001"))
        self.assertEquals(0, item.find_committed_for_order("ORD001")["WHSE001"].quantity,
                          "Item quantities do not reflect verification count")
        self.assertEquals(0, item.find_committed_for_order("ORD001")["WHSE001"].unverified_quantity,
                          "Item quantities do not reflect verification count")
        self.assertEquals(4, item.quantity_backordered("ORD001"), "Backorder should have been created")
        self.assertEquals(5, item.quantity_lost(), "Incorrect number of lost items tracked")

    def test_commit_with_overstocked_verify(self):
        item = InventoryItemFactory.build(on_hand_buffer=2)
        item.enter_stock_on_hand(5, "WHSE001")

        item.commit(4, "WHSE001", "ORD001")

        self.assertEquals(1, item.effective_quantity_on_hand("WHSE001"))
        self.assertEquals(3, item.find_committed_for_order("ORD001")["WHSE001"].quantity,
                          "Incorrect quantity was automatically verified")
        self.assertEquals(1, item.find_committed_for_order("ORD001")["WHSE001"].unverified_quantity,
                          "Incorrect quantity was automatically verified")

        # We found an extra to make 6
        item.verify_stock_level(6, "WHSE001")


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

class InventoryPurchaseOrderTestCase(TestCase):

    def test_purchase_order_delivery(self):
        item = InventoryItemFactory.build()

        next_week = datetime.datetime.now() + datetime.timedelta(weeks=1)
        next_month = datetime.datetime.now() + datetime.timedelta(weeks=4)

        item.purchase_item(10, "PO001", eta_date=next_week)
        item.purchase_item(5, "PO002", eta_date=next_month)

        self.assertEquals(10, item.quantity_purchased(purchase_order_id="PO001"), "Should have 10 items on PO001")
        self.assertEquals(5, item.quantity_purchased(purchase_order_id="PO002"), "Should have 5 items on PO002")
        self.assertEquals(15, item.quantity_purchased(), "Should have 15 items in total on purchase order")

        item.deliver_purchase_order(9, "WHSE001", "PO001")

        self.assertEquals(1, item.quantity_purchased(purchase_order_id="PO001"), "Should now have 1 item on PO001")
        self.assertEquals(6, item.quantity_purchased(), "Should 6 items in total remaining on purchase order")
        self.assertEquals(9, item.effective_quantity_on_hand(), "Should now be 9 items on hand")

        item.deliver_purchase_order(5, "WHSE001", "PO002")

        self.assertEquals(0, item.quantity_purchased(purchase_order_id="PO002"), "PO002 should be empty")
        self.assertEquals(1, item.quantity_purchased(), "Should 1 item in total remaining on purchase order")
        self.assertEquals(14, item.effective_quantity_on_hand(), "Should now be 14 items on hand")

        # re-delivery should fail
        item.deliver_purchase_order(1, "WHSE001", "PO002")
        self.assertEquals(0, item.quantity_purchased(purchase_order_id="PO002"), "PO002 should be empty")
        self.assertEquals(1, item.quantity_purchased(), "Should 1 item in total remaining on purchase order")
        self.assertEquals(14, item.effective_quantity_on_hand(), "Should now be 14 items on hand")

        # cancel remaining item on PO001
        item.cancel_purchase_order("PO001")
        self.assertEquals(0, item.quantity_purchased(purchase_order_id="PO001"), "PO001 should be empty")
        self.assertEquals(0, item.quantity_purchased(), "No purchase orders should remain")
        self.assertEquals(14, item.effective_quantity_on_hand(), "Should now be 14 items on hand")

class InventoryLostAndFoundTestCase(TestCase):

    def test_lost_and_found(self):
        item = InventoryItemFactory.build()
        item.enter_stock_on_hand(10, "WHSE001")
        item.enter_stock_on_hand(5, "WHSE002")

        self.assertEquals(15, item.effective_quantity_on_hand(), "On hand count should be initialised to 15")

        item.lost_stock(1, "WHSE001")
        self.assertEquals(14, item.effective_quantity_on_hand(), "On hand count should have reduced to 14")
        self.assertEquals(9, item.effective_quantity_on_hand(warehouse="WHSE001"),
            "On hand count for WHSE001 should have reduced to 9")

        item.found_stock(2, "WHSE001")
        self.assertEquals(16, item.effective_quantity_on_hand(), "On hand count should have increased to 16")

        item.lost_stock(1, "WHSE002")
        self.assertEquals(15, item.effective_quantity_on_hand(), "On hand count should have reduced to 15")
        self.assertEquals(4, item.effective_quantity_on_hand(warehouse="WHSE002"),
            "On hand count for WHSE002 should have reduced to 4")

        self.assertEquals(2, item.quantity_lost(), "Total lost count should be 2")
        self.assertEquals(1, item.quantity_lost("WHSE001"), "Total lost count for WHSE001 should be 1")
        self.assertEquals(1, item.quantity_lost("WHSE002"), "Total lost count for WHSE001 should be 1")
        self.assertEquals(2, item.quantity_found(), "Total found count should be 2")
        self.assertEquals(2, item.quantity_found("WHSE001"), "Total found count for WHSE001 should be 2")
        self.assertEquals(0, item.quantity_found("WHSE002"), "Total found count for WHSE002 should be 0")
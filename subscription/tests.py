import datetime
import braintree
from django.test import TestCase

from accounts.models import User
from subscription.models import Subscription
from .views import handle_subscription_webhook


class SubscriptionWebhookTestCase(TestCase):
    def setUp(self) -> None:
        braintree_configuration = braintree.Configuration(
            braintree.Environment.Sandbox,  # type: ignore
            merchant_id="123",
            public_key="123",
            private_key="123",
        )
        # create a mock BraintreeSubscription
        self.braintree_subscription_with_paid_through_date = braintree.Subscription(
            gateway=braintree.BraintreeGateway(braintree_configuration),
            attributes={
                "id": "test_subscription_id",
                "paid_through_date": datetime.date(2022, 7, 1),
            },
        )

        self.braintree_subscription_without_paid_through_date = braintree.Subscription(
            gateway=braintree.BraintreeGateway(braintree_configuration),
            attributes={
                "id": "test_subscription_id",
            },
        )

        # Create a User and Subscription
        self.user = User.objects.create_user(  # type: ignore
            email="test@user.com",
            password="testpassword",
        )

        self.subscription = Subscription.objects.create(
            user=self.user,
            braintree_subscription_id="test_subscription_id",
            end_date=datetime.date(2021, 1, 1),
        )

    def test_handle_subscription_webhook_with_paid_through_date(self) -> None:
        handle_subscription_webhook(
            self.braintree_subscription_with_paid_through_date,
        )

        self.subscription.refresh_from_db()

        self.assertEqual(
            self.subscription.end_date,
            datetime.date(2022, 7, 6),
        )

    def test_handle_subscription_webhook_without_paid_through_date(self) -> None:
        handle_subscription_webhook(
            self.braintree_subscription_without_paid_through_date,
        )

        self.subscription.refresh_from_db()

        self.assertEqual(
            self.subscription.end_date,
            datetime.date(2022, 1, 6),
        )

    def tearDown(self) -> None:
        self.subscription.delete()
        self.user.delete()
        return super().tearDown()


class SubscriptionTestCase(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(  # type: ignore
            email="test@user.com",
            password="testpassword",  # pragma: no cover
        )

    def test_subscription(self) -> None:
        # Test all possible permutations of the subscriber_given_name and
        # subscriber_family_name fields
        given_names = ["", "John"]
        family_names = ["", "Woolman"]

        for name in given_names:
            for lastname in family_names:
                subscription = Subscription.objects.create(
                    subscriber_given_name=name,
                    subscriber_family_name=lastname,
                    user=self.user,
                )

                # If name and lastname are empty, full_name should return a space
                if name == "" and lastname == "":
                    expected_full_name = ""
                    self.assertEqual(
                        subscription.subscriber_full_name,
                        expected_full_name,
                    )

                # If only lastname is empty, full_name should return just the name
                elif lastname == "":
                    self.assertEqual(
                        subscription.subscriber_full_name,
                        name,
                    )

                # If only name is empty, full_name should return just the lastname
                elif name == "":
                    self.assertEqual(
                        subscription.subscriber_full_name,
                        lastname,
                    )

                # If both are not empty, full_name should return name and lastname
                else:
                    self.assertEqual(
                        subscription.subscriber_full_name,
                        f"{name} {lastname}",
                    )

                # delete the subscription
                subscription.delete()

    def test_subscription_str(self) -> None:
        subscription = Subscription.objects.create(
            id=123,
            user=self.user,
            braintree_subscription_id="test_subscription_id",
        )

        expected_subscription_str = "Subscription 123"

        self.assertEqual(
            str(subscription),
            expected_subscription_str,
        )

        # delete the subscription
        subscription.delete()

    def tearDown(self) -> None:
        self.user.delete()
        return super().tearDown()

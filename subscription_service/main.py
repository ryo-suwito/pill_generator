import grpc
from concurrent import futures
import time
import os
import etcd3
from proto import subscription_pb2
from proto import subscription_pb2_grpc

class SubscriptionService(subscription_pb2_grpc.SubscriptionServiceServicer):
    def __init__(self, etcd_client=None):
        if etcd_client:
            self.etcd = etcd_client
        else:
            # Connect to etcd
            # host = os.environ.get("ETCD_HOST", "localhost")
            # port = int(os.environ.get("ETCD_PORT", 2379))
            # self.etcd = etcd3.client(host=host, port=port)
            pass

    def Burn(self, request, context):
        pill_id = request.pill_id
        print(f"Attempting to burn pill: {pill_id}")

        if not self.etcd:
             print("Etcd client not initialized.")
             return subscription_pb2.BurnResponse(success=False, message="Etcd unavailable")

        # Atomic CAS logic
        # We use etcd3.transactions classes directly

        try:
            # Check if key version is 0 (does not exist)
            compare = [
                etcd3.transactions.Version(pill_id) == 0
            ]

            # If true (key doesn't exist), put 'burnt'
            success_ops = [
                etcd3.transactions.Put(pill_id, "burnt")
            ]

            # If false (key exists), get the value (optional, just to return something)
            failure_ops = [
                etcd3.transactions.Get(pill_id)
            ]

            success, responses = self.etcd.transaction(
                compare=compare,
                success=success_ops,
                failure=failure_ops
            )

            if success:
                print(f"Pill {pill_id} burnt successfully.")
                return subscription_pb2.BurnResponse(success=True, message="Pill burnt")
            else:
                print(f"Pill {pill_id} already burnt (Double Spend detected).")
                return subscription_pb2.BurnResponse(success=False, message="Double spend detected")
        except Exception as e:
            print(f"Etcd error: {e}")
            return subscription_pb2.BurnResponse(success=False, message=str(e))

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Try to connect to etcd
    try:
        etcd_host = os.environ.get("ETCD_HOST", "localhost")
        etcd_port = int(os.environ.get("ETCD_PORT", 2379))
        client = etcd3.client(host=etcd_host, port=etcd_port)
    except Exception as e:
        print(f"Could not connect to real etcd: {e}")
        client = None

    subscription_pb2_grpc.add_SubscriptionServiceServicer_to_server(
        SubscriptionService(etcd_client=client), server
    )
    server.add_insecure_port('[::]:50051')
    print("Subscription Service started on port 50051")
    server.start()
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()

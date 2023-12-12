import xmlrpc.server
# import sm_backend.models.tflog_reg
import sm_backend.models.calls

server = xmlrpc.server.SimpleXMLRPCServer(("0.0.0.0", 8000))
# server.register_instance(sm_backend.models.tflog_reg.TorchLogisticRegression())
# server.register_instance(A())
server.register_instance(sm_backend.models.calls.Calls())
server.serve_forever()

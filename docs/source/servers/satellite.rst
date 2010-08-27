################
Satellite Server
################

A standard configuration includes a single instance of the satellite
server running on machine that will have processes running which will
be using helios clients to record events.

The satellite server receives events from the client(s) running on the
same machine and forwards them to one or more instances of the
:doc:`collection`.

By default all helios clients expect to connect to the satellite
server on port 2112 of localhost to deliver messages.  The listen port
of the satellite server can be changed on the command line but in an
ideal world it would be left at the default of 2112 so that the
individual :doc:`../clients/index` require zero configuration.

The satellite server takes two optional parameters (-s/--remote-server
and -p/--remote-port) that control where it will attempt to deliver
events that are posted to it.  The default is localhost:5150 and this
would work in a single-node configuration (e.g. for testing or
development).  If however the single node configuration were deployed
in production then the satellite server would server no purpose and
instead the collection server should probably just be configured to
listen on 2112.



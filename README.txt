This is a very nascent attempt at creating an alternative to syslog
that is more application oriented (as opposed to systems oriented).

Specific the goals are:

* Make it extremely easy to use from any part of any app code.

* Minimize the impact to application performance (e.g. queue requests
  and process them out of band).

* High level fault tolerance (spool to local files in the case of network
  failures, etc).

* Provide a powerful interface for searching/filtering logged events
  based on the structure of the events.

* Provide a likable interface for doing standard reporting operations
  on collected events.

* Scale lots.

We will likely be developing the python client first and foremost and
that is what we would like to use at our day job but we definitely
welcome submissions for other languages from other contributors.

I would need to write a lot more to fully express the reasoning behind
our experimenting with this approach and I think a working prototype
will do a better job of demonstrating so I am going to focus my time
on getting things working rather than writing a better description.
Maybe by then if no one else has written a better description, I'll try.

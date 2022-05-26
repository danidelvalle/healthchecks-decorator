.. code:: python

   from healthchecks_decorator import healthcheck

   @healthcheck(url="https://hc-ping.com/<uuid1>")
   def job():
      """Job with a success healthcheck signal when done"""
      pass


   @healthcheck(url="https://hc-ping.com/<uuid2>", send_start=True)
   def job_with_start():
      """Send also a /start signal before starting"""
      pass


   @healthcheck(url="https://hc-ping.com/<uuid3>")
   def job_with_exception():
      """This will produce a /fail signal"""
      raise Exception("I'll be propagated")


   @healthcheck(url="https://hc-ping.com/<uuid4>", send_diagnostics=True)
   def job_with_diagnostics():
      """Send the returned value in the POST body.
      The returned value must be a valid input for `urllib.parse.urlencode`.
      Otherwise, nothing will be sent."""
      return {"temperature": -7}

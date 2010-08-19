require 'json'
require 'net/http'


module Helios
end


class Helios::Event
  attr_accessor :timestamp, :event_type, :args
end


class Helios::AbstractClient
  def initialize
    @queue = Queue.new
    @started = false
    @thread = nil
  end

  def record_event(event)
    puts "enqueuing..."
    puts "thread: #{@thread}"
    @queue.push(event)
    @thread.run
  end

  def qsize
    @queue.size
  end

  def retry_event(event)
    # Copying the python client for now which has a comment here talking
    # about long term changes.
    record_event(event)
  end

  def record(kwargs)
    raise "pls to be providing :event kwargs" if kwargs[:event_type].nil?
    kwargs = kwargs.clone

    event = Helios::Event.new
    event.timestamp = Time.now
    event.event_type = kwargs.delete(:event_type)
    event.args = kwargs
    puts "delegating to record_event"
    record_event(event)
  end

  def process_queue
    puts "process_queue"
    loop do
      puts "Waiting on queue..."
      event = @queue.pop
      puts "Got an event: #{event}"
      retry_event(event) if not process_event(event)
    end
  end

  def process_event(event)
    # must be implemented by subclasses
    raise NotImplementedError
  end

  def start
    return false if @started
    @started = true

    puts "Starting..."
    Thread.abort_on_exception = true
    @thread = Thread.new { process_queue }
    puts "after thread new: #{@thread.alive?} #{@queue.num_waiting}"
    puts "[after] thread: #{@thread}"
    # How do we make it a daemon? Do we even want to do that?  See the
    # abstractclient in python for more discussion.
    return true
  end
end

class Helios::AbstractHTTPClient < Helios::AbstractClient
  def build_url_and_data(event)
    url = build_url
    data = build_data(event)
    return url, data
  end

  private

  def build_url
    # TODO: Configurize
    return "http://localhost:5000/event/create"
  end

  def build_data(event)
    data = {
      "ts" => event.timestamp,
      "type" => event.event_type,
      "args" => event.args}
    return JSON.generate(data)
  end
end

class Helios::Client < Helios::AbstractHTTPClient
  def process_event(event)
    puts "Processing event #{event}"
    url, data = self.build_url_and_data(event)
    url = URI.parse(url)
    headers = {"Content-Type" => "application/json"}
#    req = Net::HTTP::Post.new(url.path, data, headers)

#    req.set_form_data(data)
    # TODO: Error handling/retries
#    Net::HTTP.new(url.host, url.port).start { |http| http.request(req) }
    Net::HTTP.new(url.host, url.port).post(url.path, data, headers)
  end
end


module Helios
  CLIENT = Helios::Client.new
  CLIENT.start
end




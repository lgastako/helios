require 'rubygems'
require 'helios'
require 'optparse'


def run_example(client, delay, values, quit_after_secs)
  start = Time.now if quit_after_secs
  values = (values or {})
  count = 0
  loop do
    timestamp = Time.now
    puts "Recording event with timestamp: #{timestamp}"
    puts "Queue size: #{client.qsize}"
    kwargs = {"app_timestamp" => timestamp}
    kwargs.merge!(values)
    kwargs[:event_type] = "clock_tick"
    client.record(kwargs)
    sleep(delay)
    count += 1
    if quit_after_secs and start and Time.now - start > quit_after_secs:
        break
    end
  end
  count
end


def main
  options = {
    :debug => false,
    :json => nil,
    :delay => 1,
    :quit_after_secs => 0
  }

  OptionParser.new do |opts|
    opts.banner = "Usage: examples.rb [options]"

    opts.on("-d", "--delay SECS", "Specify delay") do |d|
      options[:delay] = d.to_f
    end

    opts.on("-j", "--json JSON", "Specify json to be added to event") do |json|
      options[:json] = json
    end

    opts.on("-v", "--debug", "Enable debugging") do
      options[:debug] = true
    end

    opts.on("-q", "--quit-after SECS", "Specify secs to quit after") do |qas|
      options[:quit_after_secs] = qas.to_f
    end
  end.parse!

  raise "i got no beef with you" if ARGV.length > 0

  delay = options[:delay]
  quit_after_secs = options[:quit_after_secs]
  values = options[:json]
  values = JSON.parse(values) if values

  client = Helios::CLIENT
  start = Time.now
  count = run_example(client, delay, values, quit_after_secs)
  diff = Time.now - start
  qps = count.to_f / diff

  puts "Posted #{count} events in #{diff} seconds for #{qps} qps"
end


main if __FILE__ == $0

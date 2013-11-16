# A sample Guardfile
# More info at https://github.com/guard/guard#readme

# Add files and commands to this file, like the example:
#   watch(%r{file/path}) { `command(s)` }
#
guard 'shell' do
  watch(/server.py/) {
    `pkill -15 server.py`
    pid = Process.spawn("./server.py -p 9000")
    Process.detach pid
  }
end

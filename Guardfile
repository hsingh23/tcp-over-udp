# A sample Guardfile
# More info at https://github.com/guard/guard#readme

# Add files and commands to this file, like the example:
#   watch(%r{file/path}) { `command(s)` }
#
guard 'shell' do
  watch(/util.py/) {
    `pkill -15 sender.py`
    pid = Process.spawn("python sender.py -p 9100 -d localhost -f sender.py")
    Process.detach pid
  }
end

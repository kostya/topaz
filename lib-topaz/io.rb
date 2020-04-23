class IO
  class << self
    alias for_fd new
  end

  def <<(s)
    write(s)
    return self
  end

  def puts(*args)
    if args.empty?
      write("\n")
      return nil
    end

    args.flatten.each do |string|
      string = string.to_s unless string.is_a?(String)
      write(string)
      write("\n") unless string[-1] == "\n"
    end
    nil
  end

  def pos=(i)
    seek(i, IO::SEEK_SET)
  end

  def each_line(sep = $/, limit = nil)
    if sep.is_a?(Fixnum) && limit.nil?
      limit = sep
      sep = $/
    end

    if sep.nil?
      yield(limit ? read(limit) : read)
      return self
    end

    sep = Topaz.convert_type(sep, String, :to_str)

    if limit == 0
      raise ArgumentError.new("invalid limit: 0 for each_line")
    end

    line = ""
    line_len = 0
    sep_length = sep.length
    sep_length = 1 if sep_length == 0

    topaz_buffered_read do |buffer|
      pos_start = 0
      while pos_start < buffer.length
        pos_end = buffer.index(sep, pos_start)

        if pos_end && pos_end >= 0
          finded = true
          pos_end += sep_length - 1
        else
          finded = false
          pos_end = buffer.length - 1
        end
        pos_len = pos_end - pos_start + 1

        if limit && ((line_len + pos_len) > limit)
          pos_len = limit - line_len
          finded = true
        end

        if finded
          if line_len == 0
            yield buffer[pos_start, pos_len]
          else
            line += buffer[pos_start, pos_len]
            yield line
            line = ""
            line_len = 0
          end
        else
          line += buffer[pos_start, pos_len]
          line_len += pos_len
        end

        pos_start += pos_len
      end
    end

    yield line if line_len > 0

    self
  end
  alias each each_line
  alias lines each_line

  def readline(sep = $/, limit = nil)
    line = gets(sep, limit)
    raise EOFError.new("end of file reached") if line.nil?
    line
  end

  def gets(sep = $/, limit = nil)
    if sep.nil?
      return read
    end
    if sep.is_a?(Fixnum) && limit.nil?
      limit = sep
      sep = $/
    end
    raise IOError.new("closed stream") if closed?
    line = ""
    loop do
      c = getc
      break if c.nil? || c.empty?
      line << c
      break if c == sep || line.length == limit
    end
    $_ = line
    line.empty? ? nil : line
  end

  def readlines(sep = $/, limit = nil)
    lines = []
    each_line(sep, limit) { |line| lines << line }
    return lines
  end

  def self.read(name)
    File.open(name) do |f|
      f.read
    end
  end

  def self.readlines(name, *args)
    File.open(name) do |f|
      return f.readlines(*args)
    end
  end

  def self.popen(cmd, mode = 'r', opts = {}, &block)
    r, w = IO.pipe
    if mode != 'r' && mode != 'w' && mode != 'rb' && mode != 'wb'
      raise NotImplementedError.new("mode #{mode} for IO.popen")
    end

    pid = fork do
      if mode == 'r'
        r.close
        $stdout.reopen(w)
      else
        w.close
        $stdin.reopen(r)
      end
      exec(*cmd)
    end

    if mode == 'r'
      res = r
      w.close
    else
      res = w
      r.close
    end

    res.instance_variable_set("@pid", pid)
    block ? yield(res) : res
  end

  def self.binread(filename, length=nil, offset=0)
    File.open(filename, "rb") do |f|
      f.seek(offset)
      if length.nil?
        f.read
      else
        f.read(length)
      end
    end
  end

  def pid
    @pid
  end

  def self.try_convert(arg)
    Topaz.try_convert_type(arg, IO, :to_io)
  end

  def getbyte
    if ch = getc
      return ch.ord
    else
      return nil
    end
  end

private

  def topaz_buffered_read(buffer_size = Topaz::IO_EACH_LINE_READ_BUFFER_SIZE)
    loop do
      buf = read(buffer_size)
      break if !buf || buf.length == 0
      yield buf
    end
  end
end

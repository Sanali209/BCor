
# function for grabing sumstrinf from string start_time marker to end marker
def get_substr_between_markers(string, start_marker, end_marker):
    start = string.index(start_marker) + len(start_marker)
    end = string.index(end_marker, start)
    return string[start:end]
"""
<form method="post" enctype="multipart/form-data"
action="http://vm02.iucr.org/cgi-bin/checkcif.pl">File name:<br>
<input type="file" name="file" size="35">
<input type="hidden" name="runtype" checked="checked" value="symmonly">
<input type="hidden" name="referer" checked="checked" value="checkcif_server">
<br>
<input type="submit" name="UPLOAD" value="Send CIF for checking">
<p>Select form of checkCIF report</p>

<input type="radio" name="outputtype" value="HTML" checked="checked">HTML
<input type="radio" name="outputtype" value="PDF">PDF
</form>
"""
import urllib2_file
import urllib2

filename = open("%s"%("/home/xray/sucrose.cif"))
params = {
                           "runtype": "symmonly",
                           "referer": "checkcif_server",
                           "outputtype": "html",
                           "file": filename
}
f = urllib2.urlopen("http://vm02.iucr.org/cgi-bin/checkcif.pl", params)
print f.read()
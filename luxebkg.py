from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import os
import math
import subprocess
import array
import numpy as np
import pprint
import ROOT
from ROOT import TFile, TTree, TH1D, TH2D, TLorentzVector, TVector3, TCanvas, TLegend, TLatex

# ROOT.gROOT.LoadMacro("LuxeStyle.C")
# ROOT.gROOT.LoadMacro("LuxeLabels.C")
# SetLuxeStyle()

ROOT.gROOT.SetBatch(1)
ROOT.gStyle.SetOptFit(0);
ROOT.gStyle.SetOptStat(0);
ROOT.gStyle.SetPadBottomMargin(0.15)
ROOT.gStyle.SetPadLeftMargin(0.13)

### for pretty prints..
pp = pprint.PrettyPrinter(indent=4)

### output dir for plots
p = subprocess.Popen("mkdir -p plots", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err = p.communicate()

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1molt9Q-2Lw63URdPhqp7A0gHZFpEMyrQ0I1tAYnz2KY'

# just an example of one spreadsheet name+range
SAMPLE_RANGE_NAME = 'DETIDs!A1:G'

# all spreadsheets' name+range
# DICT_SAMPLE_RANGE_NAME = {
#    'DETIDs':'A1:G',
#    'g+laser bkg, beamonly':'A1:K',
#    'e+laser bkg, JETI40':'A1:K',
#    'e+laser bkg, beamonly':'A1:K',
#    'e+laser bkg, PhaseII':'A1:K',
# }

DICT_SAMPLE_RANGE_NAME = {
   'g+laser bkg, beamonly' :{'Detectors':'B2:B1000', 'Nparticles':'C2:E', 'Esum':'I2:K'},
   'e+laser bkg, beamonly' :{'Detectors':'B2:B1000', 'Nparticles':'C2:E', 'Esum':'I2:K'},
   'e+laser bkg, JETI40'   :{'Detectors':'B2:B1000', 'Nparticles':'C2:E', 'Esum':'I2:K'},
   'e+laser bkg, PhaseII'  :{'Detectors':'B2:B1000', 'Nparticles':'C2:E', 'Esum':'I2:K'},
}

DICT_SAMPLE_TITLE = {
   'g+laser bkg, beamonly' : 'photon+laser, beam only',
   'e+laser bkg, beamonly' : 'electron+laser, beam only',
   'e+laser bkg, JETI40'   : 'electron+laser, JETI40'  ,
   'e+laser bkg, PhaseII'  : 'electron+laser, PhaseII' ,
}

histos = {}

#########################################################################
#########################################################################
#########################################################################


def gevalues(service,sheetid,sheetrange,doprint=True):
   # Call the Sheets API
   sheet = service.spreadsheets()
   result = sheet.values().get(spreadsheetId=sheetid, range=sheetrange).execute()
   values = result.get('values', [])
   if not values: print('No data found.')
   else:
      if(doprint):
         print("\n--------- Sheet:",sheetrange)
         for row in values: print(row)
   return values


def getservice():
   """Shows basic usage of the Sheets API. Prints values from a sample spreadsheet."""
   creds = None
   # The file token.pickle stores the user's access and refresh tokens, and is
   # created automatically when the authorization flow completes for the first
   # time.
   if os.path.exists('token.pickle'):
      with open('token.pickle', 'rb') as token:
         creds = pickle.load(token)
   # If there are no (valid) credentials available, let the user log in.
   if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
         creds.refresh(Request())
      else:
         flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
         creds = flow.run_local_server(port=0)
         # Save the credentials for the next run
         with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
   service = build('sheets', 'v4', credentials=creds)
   return service


def getdata(service,doprint=False,spreadsheetid="",rangename=""):
   data = {}
   if(spreadsheetid!="" and rangename!=""):
      ### get the data of one spreadsheet
      sheet = gevalues(service,spreadsheetid,rangename,doprint)
      sheetname = rangename.split("!")[0]
      data.update({sheetname:sheet})
   else:
      ### get the data of one spreadsheet
      # for sheetname,rangename in DICT_SAMPLE_RANGE_NAME.items():
      #    sheetrange = sheetname+"!"+rangename
      #    sheet = gevalues(service,SAMPLE_SPREADSHEET_ID,sheetrange,doprint)
      #    sheetname = sheetrange.split("!")[0]
      #    data.update({sheetname:sheet})
      for sheetname,ranges in DICT_SAMPLE_RANGE_NAME.items():
         data.update({sheetname:{}})
         for typename,typerange in ranges.items():
            print("typename="+typename+" typerange="+typerange)
            sheetrange = sheetname+"!"+typerange
            # sheetname  = sheetrange.split("!")[0]+" "+typename
            dataname = sheetname+" "+typename
            print("getting dataname="+dataname+" with range "+sheetrange)
            sheet = gevalues(service,SAMPLE_SPREADSHEET_ID,sheetrange,doprint)
            data[sheetname].update({typename:sheet})
   return data


def minmax(h1,h2,logy,forceh1min=False,fup=10,fdown=5):
   hmax = h1.GetMaximum() if(h1.GetMaximum()>h2.GetMaximum()) else h2.GetMaximum()
   hmin = 1e20
   if(forceh1min): hmin = h1.GetMinimum()
   for x in range(h1.GetNbinsX()):
      y1 = h1.GetBinContent(x)
      y2 = h2.GetBinContent(x)
      if(y1<hmin):
         if(logy):
            if(y1>0): hmin = y1
         else: hmin = y1
      if(y2<hmin):
         if(logy):
            if(y2>0): hmin = y2
         else: hmin = y2

   h1.SetMinimum(hmin/fdown)
   h2.SetMinimum(hmin/fdown)
   h1.SetMaximum(hmax*fup)
   h2.SetMaximum(hmax*fup)
   return hmin/fdown,hmax*fup
      

def LUXE(x,y,col=ROOT.kBlack,boldit=False):
   s = TLatex()
   s.SetNDC(1)
   s.SetTextAlign(42)
   s.SetTextFont(52)
   s.SetTextColor(col)
   s.SetTextSize(0.044)
   s.DrawLatex(x,y,"LUXE #it{CDR}")

def label(text,x,y,col=ROOT.kBlack,boldit=False):
   s = TLatex()
   s.SetNDC(1)
   s.SetTextAlign(42)
   s.SetTextFont(42)
   s.SetTextColor(col)
   s.SetTextSize(0.044)
   s.DrawLatex(x,y,text)


def draw(var,basename,sheetname,allpdf):
   cnv = TCanvas("cnv","",800,500)
   cnv.cd()
   cnv.SetTicks(0,1)
   cnv.SetGrid(0,1)
   cnv.SetLogy()
   hmin,hmax = minmax(histos[basename+"_gam"+var],histos[basename+"_ele"+var],True)
   hmin,hmax = minmax(histos[basename+"_gam"+var],histos[basename+"_pos"+var],True,True)
   hmin,hmax = minmax(histos[basename+"_ele"+var],histos[basename+"_pos"+var],True,True)
   histos[basename+"_gam"+var].SetLineColor(ROOT.kRed)
   histos[basename+"_ele"+var].SetLineColor(ROOT.kBlack)
   histos[basename+"_pos"+var].SetLineColor(ROOT.kBlue)
   
   histos[basename+"_gam"+var].SetFillColorAlpha(ROOT.kRed,0.5)
   histos[basename+"_ele"+var].SetFillColorAlpha(ROOT.kBlack,0.5)
   histos[basename+"_pos"+var].SetFillColorAlpha(ROOT.kBlue,0.5)
   
   # histos[basename+"_gam"+var].SetMarkerColor(ROOT.kBlack)
   # histos[basename+"_ele"+var].SetMarkerColor(ROOT.kRed)
   # histos[basename+"_pos"+var].SetMarkerColor(ROOT.kBlue)
   # histos[basename+"_gam"+var].SetMarkerStyle(20)
   # histos[basename+"_ele"+var].SetMarkerStyle(22)
   # histos[basename+"_pos"+var].SetMarkerStyle(23)
   htitle = DICT_SAMPLE_TITLE[sheetname]
   ytitle = "Particles/BX" if("nperbx" in var) else "#SigmaE/BX [GeV]"
   # histos[basename+"_gam"+var].SetTitle(htitle)
   histos[basename+"_gam"+var].GetYaxis().SetTitle(ytitle)
   # histos[basename+"_gam"+var].Draw("p")
   # histos[basename+"_ele"+var].Draw("psame")
   # histos[basename+"_pos"+var].Draw("psame")
   histos[basename+"_gam"+var].Draw("hist")
   histos[basename+"_ele"+var].Draw("hist same")
   histos[basename+"_pos"+var].Draw("hist same")
   leg = TLegend(0.74,0.70,0.91,0.88)
   leg.SetFillStyle(4000) # will be transparent
   leg.SetFillColor(0)
   leg.SetTextFont(42)
   leg.SetBorderSize(0)
   # leg.AddEntry(histos[basename+"_gam"+var],"Photons","p")
   # leg.AddEntry(histos[basename+"_ele"+var],"Electrons","p")
   # leg.AddEntry(histos[basename+"_pos"+var],"Positrons","p")
   leg.AddEntry(histos[basename+"_gam"+var],"Photons","f")
   leg.AddEntry(histos[basename+"_ele"+var],"Electrons","f")
   leg.AddEntry(histos[basename+"_pos"+var],"Positrons","f")
   leg.Draw("same")
   LUXE(0.22,0.85,ROOT.kBlack)
   htitle = htitle.split(", ")
   label(htitle[0],0.22,0.80,ROOT.kBlack)
   label(htitle[1],0.22,0.75,ROOT.kBlack)
   cnv.RedrawAxis()
   cnv.Update()
   cnv.SaveAs("plots/"+basename+var+".pdf")
   cnv.SaveAs(allpdf)
   

#########################################################################
#########################################################################
#########################################################################


def main():
   ### get the service
   service = getservice()

   doprint = False

   ### get the data of one spreadsheet
   # data = getdata(service,doprint,SAMPLE_SPREADSHEET_ID,SAMPLE_RANGE_NAME)
   # pp.pprint(data)
   # print(data)
   
   ### get the data of one spreadsheet
   data = getdata(service,doprint)
   # pp.pprint(data)
   
   allpdf = "plots/luxebkg.pdf"
   cnv = TCanvas("cnv","",800,500)
   cnv.SaveAs(allpdf+"(")
   
   binmargins = 3
   for sheetname,ranges in DICT_SAMPLE_RANGE_NAME.items():
      # pp.pprint(data[sheetname])
      detectors = data[sheetname]["Detectors"]
      nparticles = data[sheetname]["Nparticles"]
      Esum = data[sheetname]["Esum"]
      n = len(data[sheetname]["Detectors"])-1
      basename = sheetname
      basename = basename.replace(" ","_").replace("+","").replace("bkg","").replace(",","")
      for iparticle in range(len(nparticles[0])):
         particle = nparticles[0][iparticle]
         hname = basename+"_"+particle
         n4 = 4*n-1+2*binmargins
         n3 = 3*n
         histos.update( {hname+"4_nperbx"   :TH1D(hname+"4_nperbx","",n4,0,n4)} )
         histos.update( {hname+"4_esumperbx":TH1D(hname+"4_esumperbx","",n4,0,n4)} )
         histos.update( {hname+"3_nperbx"   :TH1D(hname+"3_nperbx","",n3,0,n3)} )
         histos.update( {hname+"3_esumperbx":TH1D(hname+"3_esumperbx","",n3,0,n3)} )
         histos.update( {hname+"_nperbx"    :TH1D(hname+"_nperbx","",n,0,n)} )
         histos.update( {hname+"_esumperbx" :TH1D(hname+"_esumperbx","",n,0,n)} )
         for idet in range(1,len(detectors)):
            ### set labels only once
            if(iparticle==0):
               label = detectors[idet][0] if(iparticle==0) else ""
               label = label.replace("xi","#xi")
               xbin3 = 3*idet-1
               xbin4 = -1
               if(idet==1):   xbin4 = 3*idet-1+binmargins
               elif(idet==2): xbin4 = 3*idet+binmargins
               else:          xbin4 = 4*idet-2+binmargins
               # print("iparticle="+str(iparticle)+" idet="+str(idet)+" xbin3="+str(xbin3)+" xbin4="+str(xbin4)+" label="+label)
               histos[hname+"_nperbx"].GetXaxis().SetBinLabel(idet,label)
               histos[hname+"_esumperbx"].GetXaxis().SetBinLabel(idet,label)
               histos[hname+"3_nperbx"].GetXaxis().SetBinLabel(xbin3,label)
               histos[hname+"3_esumperbx"].GetXaxis().SetBinLabel(xbin3,label)
               histos[hname+"4_nperbx"].GetXaxis().SetBinLabel(xbin4,label)
               histos[hname+"4_esumperbx"].GetXaxis().SetBinLabel(xbin4,label)
            
            ### fill
            xbin3 = 3*idet-2+iparticle
            xbin4 = -1
            if(idet==1):   xbin4 = 3*idet-2+iparticle+binmargins
            elif(idet==2): xbin4 = 3*idet-1+iparticle+binmargins
            else:          xbin4 = 4*idet-3+iparticle+binmargins
            if(len(nparticles[idet])==len(nparticles[0])):
               nperbx = float(nparticles[idet][iparticle])
               histos[hname+"_nperbx"].SetBinContent(idet,nperbx)
               histos[hname+"3_nperbx"].SetBinContent(xbin3,nperbx)
               histos[hname+"4_nperbx"].SetBinContent(xbin4,nperbx)
            if(len(Esum[idet])==len(Esum[0])):
               esumperbx = float(Esum[idet][iparticle])
               histos[hname+"_esumperbx"].SetBinContent(idet,esumperbx)
               histos[hname+"3_esumperbx"].SetBinContent(xbin3,esumperbx)
               histos[hname+"4_esumperbx"].SetBinContent(xbin4,esumperbx)

      for var in ["4_nperbx", "4_esumperbx"]: draw(var,basename,sheetname,allpdf)
      

   ### close the pdf
   cnv = TCanvas("cnv","",800,500)
   cnv.SaveAs(allpdf+")")

   ### save all histos
   tfileout = TFile("plots/luxebkg.root","RECREATE")
   tfileout.cd()
   for hname,hist in histos.items(): hist.Write()
   tfileout.Write()
   tfileout.Close()


if __name__ == '__main__':
    main()

import re 
import csv
from django.views.generic.simple import direct_to_template
from django.template.loader import render_to_string
from django.template import loader, Context
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum
import json
from collections import defaultdict

import models

def safe_div(a, b):
    try:
        return float(a) / float(b)
    except:
        return None

def safe_mul(a, b):
    try:
        return float(a) * float(b)
    except:
        return None

def scorecard(request, iso3):
    if request.GET.get("page", "1") == "1":
        return direct_to_template(request, template="oda/scorecard_front.html", extra_context={
            "iso3" : iso3
        })
    else:
        return direct_to_template(request, template="oda/scorecard_back.html", extra_context={
            "iso3" : iso3
        })

def front_data(request, iso3):
    f = open("/tmp/trace.log", "a")
    w = csv.writer(f)
    country = get_object_or_404(models.Recipient, iso3=iso3) 
    country_indicators = models.CountryIndicator.objects.filter(country=country)
    allocations = models.Allocation.objects.filter(country=country)

    hd_indicator = models.GeneralIndicator.objects.get(name="ODA for Health Disbursements (Million constant 2009 US$)")

    overrides = {
        "BLR" : {"increase" : "197%", "year" : "2005"},
        "LBY" : {"increase" : "212%", "year" : "2005"},
        "MNE" : {"increase" : "431%", "year" : "2004"},
        "UKR" : {"increase" : "31%", "year" : "2005"},
    } 
    overrides = {
        "BLR" : "2005",
        "LBY" : "2005",
        "MNE" : "2004",
        "UKR" : "2005",
    } 

    base_year = "2000" 

    if country.iso3 in overrides:
        base_year = overrides[country.iso3]
    # summary calculations
    try:
        hd_2000 = country_indicators.get(year=base_year, indicator=hd_indicator)
    except models.CountryIndicator.DoesNotExist:
        hd_2000 = 0

    try:
        hd_2010 = country_indicators.get(year="2010", indicator=hd_indicator)
    except models.CountryIndicator.DoesNotExist:
        hd_2010 = 0

    # Highest valued allocation in 2010
    alloc_2010 = allocations.filter(year="2010").order_by("-disbursement")[0]
    mdg_purpose = alloc_2010.mdgpurpose
    try:
        alloc_2000 = allocations.get(year=base_year, mdgpurpose=mdg_purpose)
    except models.Allocation.DoesNotExist:
        alloc_2000 = models.Allocation()
        alloc_2000.disbursement = 0

    sum_increase = (hd_2010.value / hd_2000.value - 1) * 100
    mdg_perc_2000 = safe_mul(safe_div(alloc_2000.disbursement, hd_2000.value), 100)
    mdg_perc_2010 = safe_mul(safe_div(alloc_2010.disbursement, hd_2010.value), 100)

    indicators = defaultdict(dict, {})
    for indicator in country_indicators:
        indicators[indicator.year][indicator.indicator.name] = indicator.value

    allocations_commitments = defaultdict(dict, {})
    allocations_disbursements = defaultdict(dict, {})
    for allocation in allocations:
        if allocation.commitment:
            allocations_commitments[allocation.year][allocation.mdgpurpose.name] = allocation.commitment;
        if allocation.disbursement:
            allocations_disbursements[allocation.year][allocation.mdgpurpose.name] = allocation.disbursement;

    js = {
        "country" : {
            "name" : country.name,
            "iso3" : country.iso3,
        }, 
        "summary" : {
            "sum_increase" : sum_increase,
            "sum_purpose" : mdg_purpose.name,
            "sum_2010" : mdg_perc_2010,
            "sum_2000" : mdg_perc_2000,
            "sum_baseyear" : base_year,
        },
        "indicators" : indicators,
        "allocations" : {
            "commitments" : allocations_commitments,
            "disbursements" : allocations_disbursements,
        },
    }

    try:
        #import pdb; pdb.set_trace()
        # sanity checks
        i1_text = "ODA for Health Commitments, (Million constant 2009 US$)"
        i2_text = "ODA for Health Disbursements (Million constant 2009 US$)"
        total_commitments1 = { year : value.get(i1_text, 0) for year, value in indicators.items() }
        total_disbursements1 = { year : value.get(i2_text, 0) for year, value in indicators.items() }
        total_commitments2 = { year : sum(ac.values()) for year, ac in allocations_commitments.items()}
        total_disbursements2 = { year : sum(ac.values()) for year, ac in  allocations_disbursements.items()}
        total_disbursements3 = models.DisbursementSource.objects.filter(country=country).aggregate(Sum('amount'))["amount__sum"]

        values = [
            country.iso3,
            total_disbursements1["2010"],
            total_disbursements3,
        ]

        for year in range(2000, 2011):
            year = str(year)
            values.append(total_commitments1.get(year, "-"))
            values.append(total_commitments2.get(year, "-"))
            values.append(total_disbursements1.get(year, "-"))
            values.append(total_disbursements2.get(year, "-"))

        w.writerow(values)

        f.flush()
    except:
        import traceback
        traceback.print_exc()
    
    f.close()
    return HttpResponse(json.dumps(js, indent=4))

def back_data(request, iso3):
    country = get_object_or_404(models.Recipient, iso3=iso3) 
    re_disb = re.compile("Other (\d+) Disb\s*")
    
    total = models.DisbursementSource.objects.filter(country=country).aggregate(Sum('amount'))["amount__sum"]
    disbursements = models.Disbursement.objects.filter(country=country)
    other_disbursements = disbursements.get(donor__contains="Other ")
    ndisb = int(re_disb.match(other_disbursements.donor).groups()[0])
    pdisb = other_disbursements.percentage
    total_disbursements_count = disbursements.count() - 1 + ndisb
    total_disbursements_sum = float(disbursements.aggregate(Sum('disbursement'))["disbursement__sum"])

    js = {
        "country" : {
            "name" : country.name,
            "iso3" : country.iso3,
        }, 
        "summary" : {
            "total_disbursements_count" : total_disbursements_count,
            "total_disbursements_sum" : total_disbursements_sum,
            "total_disbursements_from_largest" : total,
        },
        "bil_sources" : {
            ds.source : {
                "number": ds.number,
                "amount": ds.amount
            }
            for ds in models.DisbursementSource.objects.filter(country=country, group="Bil")
        },
        "mul_sources" : {
            ds.source : {
                "number": ds.number,
                "amount": ds.amount
            }
            for ds in models.DisbursementSource.objects.filter(country=country, group="Mul")
        },
        "largest_sources" : [{
               "percentage" : ds.amount / total,
               "source" : ds.source 
            }
            for ds in models.DisbursementSource.objects.filter(country=country).order_by("-amount")[0:5]
        ],
        "largest_disbursements" : [{
               "donor" : d.donor, 
               "year" : d.year, 
               "disbursement" : d.disbursement, 
               "purpose" : d.purpose, 
            }
            for d in disbursements.exclude(donor__contains="Other ").order_by("-disbursement")[0:7]
        ],
        "disbursements_percentage" : {
            "other" : {"number" : ndisb, "percentage" : pdisb},
            "largest" : {"number" : 7, "percentage" : 1 - pdisb},
        }
    }
    
    return HttpResponse(json.dumps(js, indent=4))
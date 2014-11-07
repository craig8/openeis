"""
Unit tests for Daily Summary application.


Copyright
=========

OpenEIS Algorithms Phase 2 Copyright (c) 2014,
The Regents of the University of California, through Lawrence Berkeley National
Laboratory (subject to receipt of any required approvals from the U.S.
Department of Energy). All rights reserved.

If you have questions about your rights to use or distribute this software,
please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov
referring to "OpenEIS Algorithms Phase 2 (LBNL Ref 2014-168)".

NOTICE:  This software was produced by The Regents of the University of
California under Contract No. DE-AC02-05CH11231 with the Department of Energy.
For 5 years from November 1, 2012, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, and perform
publicly and display publicly, by or on behalf of the Government. There is
provision for the possible extension of the term of this license. Subsequent to
that period or any extension granted, the Government is granted for itself and
others acting on its behalf a nonexclusive, paid-up, irrevocable worldwide
license in this data to reproduce, prepare derivative works, distribute copies
to the public, perform publicly and display publicly, and to permit others to
do so. The specific term of the license can be identified by inquiry made to
Lawrence Berkeley National Laboratory or DOE. Neither the United States nor the
United States Department of Energy, nor any of their employees, makes any
warranty, express or implied, or assumes any legal liability or responsibility
for the accuracy, completeness, or usefulness of any data, apparatus, product,
or process disclosed, or represents that its use would not infringe privately
owned rights.


License
=======

Copyright (c) 2014, The Regents of the University of California, Department
of Energy contract-operators of the Lawrence Berkeley National Laboratory.
All rights reserved.

1. Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are met:

   (a) Redistributions of source code must retain the copyright notice, this
   list of conditions and the following disclaimer.

   (b) Redistributions in binary form must reproduce the copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

   (c) Neither the name of the University of California, Lawrence Berkeley
   National Laboratory, U.S. Dept. of Energy nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

2. THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
   AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
   ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
   (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
   LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
   ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
   (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
   THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

3. You are under no obligation whatsoever to provide any bug fixes, patches,
   or upgrades to the features, functionality or performance of the source code
   ("Enhancements") to anyone; however, if you choose to make your Enhancements
   available either publicly, or directly to Lawrence Berkeley National
   Laboratory, without imposing a separate written license agreement for such
   Enhancements, then you hereby grant the following license: a non-exclusive,
   royalty-free perpetual license to install, use, modify, prepare derivative
   works, incorporate into other computer software, distribute, and sublicense
   such enhancements or derivative works thereof, in binary and source code
   form.

NOTE: This license corresponds to the "revised BSD" or "3-clause BSD" license
and includes the following modification: Paragraph 3. has been added.
"""

import os
import pytest

from openeis.applications.utest_applications.apptest import AppTestBase

pytestmark = pytest.mark.django_db

@pytest.mark.usesfixtures('daily_summary_datafile')
class TestDailySummary(AppTestBase):
    fixtures = [
        os.path.join(os.path.abspath(os.path.dirname(__file__)), 'daily_summary_fixture.json')
        ]

    def setUp(self):
        self.basedir = os.path.abspath(os.path.dirname(__file__))

    def test_daily_summary_same_numbers(self):
        ds_same_num_ini = os.path.join(self.basedir,
            'daily_summary_same_number.ini')
        ds_same_num_exp = {}
        ds_same_num_exp['Daily_Summary_Table'] = os.path.join(self.basedir,
            'daily_summary_same_number.ref.csv')
        self.run_it(ds_same_num_ini, ds_same_num_exp, clean_up=True)

    def test_daily_summary_one_to_five(self):
        ds_onetofive_ini = os.path.join(self.basedir,
            'daily_summary_onetofive.ini')
        ds_onetofive_exp = {}
        ds_onetofive_exp['Daily_Summary_Table'] = os.path.join(self.basedir,
            'daily_summary_onetofive.ref.csv')
        self.run_it(ds_onetofive_ini, ds_onetofive_exp, clean_up=True)

    def test_daily_summary_missing_numbers(self):
        ds_missing_ini = os.path.join(self.basedir,
            'daily_summary_missing.ini')
        ds_missing_exp = {}
        ds_missing_exp['Daily_Summary_Table'] = os.path.join(self.basedir,
            'daily_summary_missing.ref.csv')
        self.run_it(ds_missing_ini, ds_missing_exp, clean_up=True)

    def test_daily_summary_floats(self):
        ds_floats_ini = os.path.join(self.basedir,
            'daily_summary_floats.ini')
        ds_floats_exp = {}
        ds_floats_exp['Daily_Summary_Table'] = os.path.join(self.basedir,
            'daily_summary_floats.ref.csv')
        self.run_it(ds_floats_ini, ds_floats_exp, clean_up=True)

    def test_daily_summary_invalid(self):
        ds_incorrect_ini = os.path.join(self.basedir,
            'daily_summary_invalid.ini')
        self.assertRaises(Exception, self.run_application, ds_incorrect_ini)

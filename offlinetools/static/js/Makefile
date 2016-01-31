# =========================================================================================
#  Copyright 2016 Community Information Online Consortium (CIOC) and KCL Software Solutions
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# =========================================================================================

.PHONY: default

default: search.min.js

%.min.js: %.js
	java -jar c:/bin/compiler.jar --compilation_level SIMPLE_OPTIMIZATIONS --js $< --create_source_map ./$<.map  > $@
	unix2dos $@

search.js: libs/json2.js libs/jquery.bgiframe.js mylibs/cached_state.js mylibs/autocomplete.js
	cat $^ > $@




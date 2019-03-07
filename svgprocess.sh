#!/bin/bash
sed -i "s%\'</style>%</style>%g" $1
/home/monkey/.cargo/bin/svgcleaner $1 $2
sed -i "s%<svg%<g%g" $2
sed -i "s%</svg%</g%g" $2
sed -i -e "0,/<g/ s/<g/<svg/" $2
sed -i "s/....$//" $2
echo "</svg>" >> $2
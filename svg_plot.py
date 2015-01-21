import svgwrite

dwg = svgwrite.Drawing(filename='hollow_test.svg', debug=True)

poly = dwg.add(dwg.polygon([(0,0), (400,0), (400,400), (0,400)]
	,stroke='black', fill='black'))
#path = svgwrite.path.Path("M20,20 L300,20 L300,300 L20,300 L20,20",
#	fill='none', stroke='black')
#dwg.add(path)
poly_2 = dwg.add(dwg.polygon([(20,20),(300,20),(300,300),(20,300)],
	stroke='black', fill='white'))

poly_3 = dwg.add(dwg.polygon([(40,40), (200,40), (200,200), (40,200)],
	stroke='black', fill='black'))



dwg.save()


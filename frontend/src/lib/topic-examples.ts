// One catalogue for the existing Explore Topics view.
export const exampleTopics = [
  {
    "title": "Equations & inequalities",
    "description": "Linear and quadratic equations, linear systems, and inequalities. For multiple variables, choose a target when prompted.",
    "review": false,
    "examples": [
      "3y + 5 = 20",
      "3n + 4 = 40",
      "x^2 - 5x + 6 = 0",
      "2x+y=7; x-y=2",
      "-2x+3>7",
      "x + y = 10"
    ]
  },
  {
    "title": "Arithmetic & functions",
    "description": "Exact arithmetic and supported functions. Angles use radians; log is the natural logarithm.",
    "review": false,
    "examples": [
      "sqrt(49)",
      "sin(pi/2)",
      "log(E)"
    ]
  },
  {
    "title": "Polynomial calculus",
    "description": "Single-variable polynomials up to degree 6 with rational coefficients.",
    "review": false,
    "examples": [
      "diff(x^3, x)",
      "integrate(x^2, x)"
    ]
  },
  {
    "title": "Matrices",
    "description": "Rational matrices up to 3×3. Inverses require a nonzero determinant.",
    "review": false,
    "examples": [
      "det([[1,2],[3,4]])",
      "inverse([[1,2],[3,4]])"
    ]
  },
  {
    "title": "Vectors",
    "description": "Numeric vectors with 2–3 components; cross products require 3.",
    "review": false,
    "examples": [
      "dot([1,2],[3,4])",
      "cross([1,0,0],[0,1,0])",
      "norm([3,4])"
    ]
  },
  {
    "title": "Word problems",
    "description": "Selected English patterns. Review and confirm the interpreted model before solving.",
    "review": true,
    "examples": [
      "Twice a number plus 3 is 11"
    ]
  },
  {
    "title": "Geometry",
    "description": "Named dimensions and basic formulas. Sentence-based questions require model review; diagrams are schematic.",
    "review": true,
    "examples": [
      "Find the area of a triangle with base 4 cm and height 6 cm",
      "circle_area(3)",
      "hypotenuse(3,4)"
    ]
  },
  {
    "title": "Statistics",
    "description": "Mean, median and population variance for bounded lists of rational values.",
    "review": false,
    "examples": [
      "mean([2,4,6])",
      "median([1,3,5,7])",
      "variance([2,4,6])"
    ]
  },
  {
    "title": "Probability & counting",
    "description": "Finite counts. Probability assumes equally likely outcomes.",
    "review": false,
    "examples": [
      "choose(5,2)",
      "probability(2,6)"
    ]
  }
];

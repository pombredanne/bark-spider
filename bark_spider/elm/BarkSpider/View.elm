module BarkSpider.View (..) where

import BarkSpider.Actions exposing (..)
import BarkSpider.Model exposing (ID, Model, SimulationResults)
import BarkSpider.Simulation as Sim
import BarkSpider.Util exposing (distinctColors)
import Bootstrap.Html exposing (..)
import Chartjs.Line exposing (..)
import Color exposing (..)
import Dict
import Html exposing (div, fromElement, Html, hr, h1, node, text)
import Html.Attributes exposing (href, rel, src)
import Html.Lazy
import String


stylesheet : String -> Html
stylesheet url =
  node "link" [ rel "stylesheet", href url ] []


script : String -> Html
script url =
  node "script" [ src url ] []


simView : Signal.Address Action -> ( ID, Sim.Simulation ) -> Html
simView address ( id, sim ) =
  Sim.view (Signal.forwardTo address (Modify id)) sim


resultToSeries : SimulationResults -> (Float -> Color) -> Series
resultToSeries result color =
  ( result.name
  , defStyle color
  , Dict.values result.data.software_development_rate
  )


resultsToChart : List SimulationResults -> Html
resultsToChart results =
  let
    res1 =
      List.head results
  in
    case res1 of
      Just res ->
        let
          config =
            ( Dict.values res.data.elapsed_time |> List.map toString
            , List.map2 resultToSeries results distinctColors
            )

          options =
            { defaultOptions
              | animation = False
              , pointDot = False
            }
        in
          chart 1000 1000 config options
            |> fromElement

      -- TODO: Insert legend. We need to add support for legends to the chartjs bindings.

      Nothing ->
        div [] []


view : Signal.Address Action -> Model -> Html
view address model =
  containerFluid_
    [ stylesheet "/static/external/css/bootstrap.min.css"
    , stylesheet "/static/external/css/bootstrap-theme.min.css"
    , stylesheet "/static/bark_spider.css"
    , script "/static/external/js/jquery.min.js"
    , script "/static/external/js/bootstrap.min.js"
    , row_
        [ colMd_
            4
            4
            4
            ([ h1 [] [ text "Simulation parameters" ]
             , row_
                [ colMd_
                    12
                    12
                    12
                    [ btnDefault' "" { btnParam | label = Just "Add parameter set" } address (AddSimulation (Sim.createSimulation "unnamed"))
                    , btnDefault' "pull-right btn-primary" { btnParam | label = Just "Run simulation" } address RunSimulation
                    ]
                ]
             , hr [] []
             ]
              ++ List.map (simView address) model.simulations
            )
        , colMd_
            8
            8
            8
            [ Html.Lazy.lazy resultsToChart model.results
            , text (String.concat model.error_messages)
            ]
        ]
    ]
